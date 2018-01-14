from collections import namedtuple
import re
from subprocess import PIPE, Popen

import pytest
from tests.native import build_native_testapp

from memaccess import MemoryView


TestProcessInfo = namedtuple('TestProcess', ('pid', 'lines'))


@pytest.fixture(scope='module')
def read_test_process():
    test_app_path = build_native_testapp('read-test-app')

    test_process = Popen(test_app_path,
                         universal_newlines=True, stdin=PIPE, stdout=PIPE)

    lines = iter(test_process.stdout.readline,
                 'Press ENTER to quit...\n')

    yield TestProcessInfo(pid=test_process.pid, lines=tuple(lines))

    test_process.stdin.write('\n')
    test_process.stdin.flush()

    test_process.wait()


def match_list(rgx, lst):
    for line in lst:
        match = re.match(rgx, line)
        if match is not None:
            return match


def test_invalid_process():
    # Trying to use process 0 raises an error according to API specs.
    with pytest.raises(RuntimeError) as ex:
        MemoryView(0)

    assert str(ex.value) == "Can't open process with pid 0, error code 87"


def test_double_close(read_test_process):
    # Double closing is invalid.
    expected_message = "Can't close process handle, error code 6"

    view = MemoryView(read_test_process.pid)
    view.close()
    with pytest.raises(RuntimeError) as ex:
        view.close()

    assert str(ex.value) == expected_message

    # Same should happen when using context manager variant.
    with MemoryView(read_test_process.pid) as view:
        pass
    with pytest.raises(RuntimeError) as ex:
        view.close()

    assert str(ex.value) == expected_message


def test_read_int(read_test_process):
    rgx = r'int: (-?\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_int(address) == value


def test_read_unsigned_int(read_test_process):
    rgx = r'unsigned int: (\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_unsigned_int(address) == value


def test_read_char(read_test_process):
    rgx = r'char: (\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    value = bytes([int(match.group(1))])
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_char(address) == value


def test_read_short(read_test_process):
    rgx = r'short: (-?\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_short(address) == value


def test_read_unsigned_short(read_test_process):
    rgx = r'unsigned short: (\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_unsigned_short(address) == value


def test_read_float(read_test_process):
    rgx = r'float: (-?\d+(?:\.\d+)?) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    value = float(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_float(address) == value


def test_read_double(read_test_process):
    rgx = r'double: (-?\d+(?:\.\d+)?) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    value = float(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_double(address) == value


def test_read(read_test_process):
    rgx = r'bytes: (\d+(?: \d+)*) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, read_test_process.lines)

    values = bytes([int(num) for num in match.group(1).split()])
    address = int(match.group(2), 16)

    with MemoryView(read_test_process.pid) as view:
        assert view.read(len(values), address) == values
