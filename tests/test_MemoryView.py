from collections import namedtuple
import re
from subprocess import PIPE, Popen

import pytest
from tests.native import build_native_testapp

from memaccess import MemoryView


TestProcessValue = namedtuple('TestProcessValue', ('type', 'value', 'address'))
TestProcessInfo = namedtuple('TestProcessInfo', ('pid', 'values'))


def match_testprocess_values(lines):
    rgx = r'(.+?): (.+) at ((?:0x)?[0-9A-Fa-f]+)'

    for line in lines:
        match = re.match(rgx, line)
        yield TestProcessValue(type=match.group(1),
                               value=match.group(2),
                               address=int(match.group(3), 16))


@pytest.fixture(scope='module')
def read_test_process():
    test_app_path = build_native_testapp('read-test-app')

    test_process = Popen(test_app_path,
                         universal_newlines=True, stdin=PIPE, stdout=PIPE)

    lines = iter(test_process.stdout.readline,
                 'Press ENTER to quit...\n')

    yield TestProcessInfo(pid=test_process.pid,
                          values=tuple(match_testprocess_values(lines)))

    test_process.stdin.write('\n')
    test_process.stdin.flush()

    test_process.wait()


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
    field = next(v for v in read_test_process.values
                 if v.type == 'int')
    value = int(field.value)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_int(field.address) == value


def test_read_unsigned_int(read_test_process):
    field = next(v for v in read_test_process.values
                 if v.type == 'unsigned int')
    value = int(field.value)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_unsigned_int(field.address) == value


def test_read_char(read_test_process):
    field = next(v for v in read_test_process.values
                 if v.type == 'char')
    value = bytes([int(field.value)])

    with MemoryView(read_test_process.pid) as view:
        assert view.read_char(field.address) == value


def test_read_short(read_test_process):
    field = next(v for v in read_test_process.values
                 if v.type == 'short')
    value = int(field.value)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_short(field.address) == value


def test_read_unsigned_short(read_test_process):
    field = next(v for v in read_test_process.values
                 if v.type == 'unsigned short')
    value = int(field.value)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_unsigned_short(field.address) == value


def test_read_float(read_test_process):
    field = next(v for v in read_test_process.values
                 if v.type == 'float')
    value = float(field.value)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_float(field.address) == value


def test_read_double(read_test_process):
    field = next(v for v in read_test_process.values
                 if v.type == 'double')
    value = float(field.value)

    with MemoryView(read_test_process.pid) as view:
        assert view.read_double(field.address) == value


def test_read(read_test_process):
    field = next(v for v in read_test_process.values
                 if v.type == 'bytes')
    values = bytes([int(num) for num in field.value.split()])

    with MemoryView(read_test_process.pid) as view:
        assert view.read(len(values), field.address) == values
