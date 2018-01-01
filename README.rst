``memaccess``
=============

Python library for Windows giving live access to a program’s memory.

Usage
-----

``memaccess`` exposes one main class to use for memory inspection:
``MemoryView``. It will request all necessary data from Windows to be
able to read memory of another application. Just pass to the class the
process-id of the application you want to observe:

.. code:: python

    from memaccess import MemoryView

    view = MemoryView(5555)
    # Read memory...
    view.close()

It’s safer to use the context-manager variant of ``MemoryView``:

.. code:: python

    from memaccess import MemoryView

    with MemoryView(5555) as view:
        pass  # Read memory...

..

    **NOTE**

    Accessing another program’s memory requires elevated privileges,
    otherwise instantiation of ``MemoryView`` will fail.

To read content, ``memaccess`` exposes the ``read`` function. It takes
the number of bytes to read and the address where to start reading.

.. code:: python

    # Read 8 bytes of memory at address 0x01234560
    view.read(8, 0x01234560)

For convenience, ``MemoryView`` exposes read methods that convert values
in memory to respective C/C++ types.

.. code:: python

    view.read_int(0x01234560)
    view.read_float(0x01234564)
    # ... and many others.

Please inspect the ``MemoryView`` class for details on all of those
functions.

Exceptions
----------

Some exceptions are raised due to internal Windows API errors and show
an error code.

::

    >>> from memaccess import MemoryView
    >>> MemoryView(5555)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      ...
    RuntimeError: Can't open process with pid 5555, error code 87

You can read up on those error codes here:

https://msdn.microsoft.com/de-de/library/windows/desktop/ms681381(v=vs.85).aspx
