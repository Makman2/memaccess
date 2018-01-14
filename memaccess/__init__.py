from ctypes import c_ulong, create_string_buffer, POINTER, windll, wintypes
import struct


_OpenProcess = windll.kernel32.OpenProcess
_OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
_OpenProcess.restype = wintypes.HANDLE

_ReadProcessMemory = windll.kernel32.ReadProcessMemory
_ReadProcessMemory.argtypes = (wintypes.HANDLE, wintypes.LPCVOID,
                               wintypes.LPVOID, c_ulong, POINTER(c_ulong))
_ReadProcessMemory.restype = wintypes.BOOL

_WriteProcessMemory = windll.kernel32.WriteProcessMemory
_WriteProcessMemory.argtypes = (wintypes.HANDLE, wintypes.LPVOID,
                                wintypes.LPCVOID, c_ulong, POINTER(c_ulong))
_WriteProcessMemory.restype = wintypes.BOOL

_CloseHandle = windll.kernel32.CloseHandle
_CloseHandle.argtypes = (wintypes.HANDLE,)
_CloseHandle.restype = wintypes.BOOL

_GetLastError = windll.kernel32.GetLastError
_GetLastError.argtypes = tuple()
_GetLastError.restype = wintypes.DWORD

_PROCESS_VM_OPERATION = 0x0008
_PROCESS_VM_READ = 0x0010
_PROCESS_VM_WRITE = 0x0020


class MemoryView:
    def __init__(self, pid, mode='r'):
        """
        Initializes a new `MemoryView`.

        A `MemoryView` exposes functions that allow to read or write memory of
        other running processes. It takes care of requesting necessary data
        from Windows to be able to access process memory.

        >>> from memaccess import MemoryView
        >>> view = MemoryView(5555)
        >>> # Read memory...
        >>> view.close()

        It's safer to use the context-manager variant of `MemoryView`, so you
        don't forget to close the object manually with `close`:

        >>> with MemoryView(5555) as view:
        >>>     pass  # Read memory...

        By default `MemoryView` only allows to read process memory, and calls
        to write-functions will fail. To also allow writes, you can supply
        opening-mode-specifiers (similar to the Python built-in function
        `open`):

        >>> with MemoryView(5555, 'rw') as view:
        >>>     pass  # Read and write memory...

        :param pid:
            The process-id of the process to observe.
        :param mode:
            The process opening mode. Supported values are `r`, `w` or a
            combination of both (`rw`).
        """
        access_level = 0x0000
        for letter in set(mode):
            if letter == 'r':
                access_level += _PROCESS_VM_READ
            elif letter == 'w':
                access_level += _PROCESS_VM_OPERATION + _PROCESS_VM_WRITE
            else:
                raise ValueError('Invalid access mode: {}'.format(mode))

        self._process_handle = _OpenProcess(access_level, False, pid)

        if self._process_handle is None:
            error_code = _GetLastError()
            raise RuntimeError(
                "Can't open process with pid {}, "
                "error code {}".format(pid, error_code))

    def close(self):
        """
        Closes the memory view.

        Calling this function on an already closed `MemoryView` raises an
        exception.
        """
        if not _CloseHandle(self._process_handle):
            error_code = _GetLastError()
            raise RuntimeError(
                "Can't close process handle, "
                "error code {}".format(error_code))

    def read(self, size, address):
        """
        Reads a piece of process memory.

        :param size:
            Number of bytes to read from the process.
        :param address:
            Memory address where to start reading from.
        :return:
            A `bytes` object containing the data read.
        """
        buffer = create_string_buffer(size)
        read_size = c_ulong()

        if not _ReadProcessMemory(self._process_handle, address, buffer, size,
                                  read_size):
            error_code = _GetLastError()
            raise RuntimeError(
                "Can't read {} bytes of process memory at address 0x{:x}, "
                "error code {}".format(size, address, error_code))

        # Check if read size and desired size fit together.
        if read_size.value != size:
            raise RuntimeError('Memory read incomplete')

        return buffer.raw

    def _read_and_convert(self, fmt, address):
        return struct.unpack(fmt, self.read(struct.calcsize(fmt), address))

    def read_int(self, address):
        """
        Reads an integer (4 bytes) from memory.

        :param address:
            Memory address where to read from.
        :return:
            Integer value at given address.
        """
        return self._read_and_convert('<i', address)[0]

    def read_unsigned_int(self, address):
        """
        Reads an unsigned integer (4 bytes) from memory.

        :param address:
            Memory address where to read from.
        :return:
            Unsigned integer value at given address.
        """
        return self._read_and_convert('<I', address)[0]

    def read_char(self, address):
        """
        Reads a char (1 byte) from memory.

        :param address:
            Memory address where to read from.
        :return:
            Char value at given address as a `bytes` object.
        """
        return self._read_and_convert('c', address)[0]

    def read_short(self, address):
        """
        Reads a short (2 bytes) from memory.

        :param address:
            Memory address where to read from.
        :return:
            Short value at given address.
        """
        return self._read_and_convert('<h', address)[0]

    def read_unsigned_short(self, address):
        """
        Reads an unsigned short (2 bytes) from memory.

        :param address:
            Memory address where to read from.
        :return:
            Unsigned short value at given address.
        """
        return self._read_and_convert('<H', address)[0]

    def read_float(self, address):
        """
        Reads a float (4 bytes) from memory.

        :param address:
            Memory address where to read from.
        :return:
            Float value at given address.
        """
        return self._read_and_convert('<f', address)[0]

    def read_double(self, address):
        """
        Reads a double (8 bytes) from memory.

        :param address:
            Memory address where to read from.
        :return:
            Double value at given address.
        """
        return self._read_and_convert('<d', address)[0]

    def write(self, values, address):
        """
        Writes bytes to given memory location.

        :param value:
            ``bytes`` to write.
        :param address:
            Memory address where to start writing.
        """
        buffer = create_string_buffer(len(values))
        buffer.raw = values
        written_size = c_ulong()

        if not _WriteProcessMemory(self._process_handle, address, buffer,
                                   len(buffer), written_size):
            error_code = _GetLastError()
            raise RuntimeError(
                "Can't write {} bytes to address 0x{:x} of process memory, "
                "error code {}".format(len(values), address, error_code))

        # Check if written size and desired size fit together.
        if written_size.value != len(values):
            raise RuntimeError('Memory write incomplete')

    def write_int(self, value, address):
        """
        Writes an integer (4 bytes) to memory.

        :param value:
            The value to write.
        :param address:
            Memory address where to write to.
        """
        self.write(struct.pack('<i', value), address)

    def write_unsigned_int(self, value, address):
        """
        Writes an unsigned integer (4 bytes) to memory.

        :param value:
            The value to write.
        :param address:
            Memory address where to write to.
        """
        self.write(struct.pack('<I', value), address)

    def write_char(self, value, address):
        """
        Writes a char (1 byte) to memory.

        :param value:
            The value to write.
        :param address:
            Memory address where to write to.
        """
        self.write(struct.pack('c', value), address)

    def write_short(self, value, address):
        """
        Writes a short (2 bytes) to memory.

        :param value:
            The value to write.
        :param address:
            Memory address where to write to.
        """
        self.write(struct.pack('<h', value), address)

    def write_unsigned_short(self, value, address):
        """
        Writes an unsigned short (2 bytes) to memory.

        :param value:
            The value to write.
        :param address:
            Memory address where to write to.
        """
        self.write(struct.pack('<H', value), address)

    def write_float(self, value, address):
        """
        Writes a float (4 bytes) to memory.

        :param value:
            The value to write.
        :param address:
            Memory address where to write to.
        """
        self.write(struct.pack('<f', value), address)

    def write_double(self, value, address):
        """
        Writes a double (8 bytes) to memory.

        :param value:
            The value to write.
        :param address:
            Memory address where to write to.
        """
        self.write(struct.pack('<d', value), address)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
