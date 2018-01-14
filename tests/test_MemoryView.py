from collections import namedtuple
import re
from subprocess import PIPE, Popen

import pytest
from tests.native import build_native_testapp

from memaccess import MemoryView


TestProcessInfo = namedtuple('TestProcess', ('pid', 'lines'))


@pytest.fixture(scope='module')
def testprocess():
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


def test_double_close(testprocess):
    # Double closing is invalid.
    expected_message = "Can't close process handle, error code 6"

    view = MemoryView(testprocess.pid)
    view.close()
    with pytest.raises(RuntimeError) as ex:
        view.close()

    assert str(ex.value) == expected_message

    # Same should happen when using context manager variant.
    with MemoryView(testprocess.pid) as view:
        pass
    with pytest.raises(RuntimeError) as ex:
        view.close()

    assert str(ex.value) == expected_message


def test_read_int(testprocess):
    rgx = r'int: (-?\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read_int(address) == value


def test_read_unsigned_int(testprocess):
    rgx = r'unsigned int: (\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read_unsigned_int(address) == value


def test_read_char(testprocess):
    rgx = r'char: (\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    value = bytes([int(match.group(1))])
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read_char(address) == value


def test_read_short(testprocess):
    rgx = r'short: (-?\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read_short(address) == value


def test_read_unsigned_short(testprocess):
    rgx = r'unsigned short: (\d+) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    value = int(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read_unsigned_short(address) == value


def test_read_float(testprocess):
    rgx = r'float: (-?\d+(?:\.\d+)?) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    value = float(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read_float(address) == value


def test_read_double(testprocess):
    rgx = r'double: (-?\d+(?:\.\d+)?) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    value = float(match.group(1))
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read_double(address) == value


def test_read(testprocess):
    rgx = r'bytes: (\d+(?: \d+)*) at ((?:0x)?[0-9A-Fa-f]+)'
    match = match_list(rgx, testprocess.lines)

    values = bytes([int(num) for num in match.group(1).split()])
    address = int(match.group(2), 16)

    with MemoryView(testprocess.pid) as view:
        assert view.read(len(values), address) == values
