from ctypes import c_ulong, create_string_buffer, POINTER, windll, wintypes
import struct


_OpenProcess = windll.kernel32.OpenProcess
_OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
_OpenProcess.restype = wintypes.HANDLE

_ReadProcessMemory = windll.kernel32.ReadProcessMemory
_ReadProcessMemory.argtypes = (wintypes.HANDLE, wintypes.LPCVOID,
                               wintypes.LPVOID, c_ulong, POINTER(c_ulong))
_ReadProcessMemory.restype = wintypes.BOOL

_CloseHandle = windll.kernel32.CloseHandle
_CloseHandle.argtypes = (wintypes.HANDLE,)
_CloseHandle.restype = wintypes.BOOL

_GetLastError = windll.kernel32.GetLastError
_GetLastError.argtypes = tuple()
_GetLastError.restype = wintypes.DWORD

_PROCESS_VM_READ = 0x0010


class MemoryView:
    def __init__(self, pid):
        self._process_handle = _OpenProcess(_PROCESS_VM_READ, False, pid)

        if self._process_handle is None:
            error_code = _GetLastError()
            raise RuntimeError(
                "Can't open process with pid {}, "
                "error code {}".format(pid, error_code))

    def close(self):
        if not _CloseHandle(self._process_handle):
            error_code = _GetLastError()
            raise RuntimeError(
                "Can't close process handle, "
                "error code {}".format(error_code))

    def read(self, size, address):
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
        return self._read_and_convert('<i', address)[0]

    def read_unsigned_int(self, address):
        return self._read_and_convert('<I', address)[0]

    def read_char(self, address):
        return self._read_and_convert('c', address)[0]

    def read_float(self, address):
        return self._read_and_convert('<f', address)[0]

    def read_double(self, address):
        return self._read_and_convert('<d', address)[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
