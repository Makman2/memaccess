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


@pytest.fixture
def write_test_process():
    it = _write_test_process_iterator()
    yield it

    # Complete the iterator and let the process iterator do cleanups.
    for _ in it:
        pass


def _write_test_process_iterator():
    test_app_path = build_native_testapp('write-test-app')

    test_process = Popen(test_app_path,
                         universal_newlines=True, stdin=PIPE, stdout=PIPE)

    lines = iter(test_process.stdout.readline,
                 'Press ENTER to continue...\n')

    yield TestProcessInfo(pid=test_process.pid,
                          values=tuple(match_testprocess_values(lines)))

    test_process.stdin.write('\n')
    test_process.stdin.flush()

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


def test_write_int(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'int')
    value1 = int(field1.value)

    new_value = 211022
    with MemoryView(process_info.pid, 'w') as view:
        view.write_int(new_value, field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'int')
    value2 = int(field2.value)

    assert field1.address == field2.address
    assert value2 != value1
    assert value2 == new_value


def test_write_unsigned_int(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'unsigned int')
    value1 = int(field1.value)

    new_value = 12000993
    with MemoryView(process_info.pid, 'w') as view:
        view.write_unsigned_int(new_value, field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'unsigned int')
    value2 = int(field2.value)

    assert field1.address == field2.address
    assert value2 != value1
    assert value2 == new_value


def test_write_char(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'char')
    value1 = int(field1.value)

    new_value = 3
    with MemoryView(process_info.pid, 'w') as view:
        view.write_char(bytes([new_value]), field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'char')
    value2 = int(field2.value)

    assert field1.address == field2.address
    assert value2 != value1
    assert value2 == new_value


def test_write_short(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'short')
    value1 = int(field1.value)

    new_value = -31000
    with MemoryView(process_info.pid, 'w') as view:
        view.write_short(new_value, field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'short')
    value2 = int(field2.value)

    assert field1.address == field2.address
    assert value2 != value1
    assert value2 == new_value


def test_write_unsigned_short(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'unsigned short')
    value1 = int(field1.value)

    new_value = 36789;
    with MemoryView(process_info.pid, 'w') as view:
        view.write_unsigned_short(new_value, field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'unsigned short')
    value2 = int(field2.value)

    assert field1.address == field2.address
    assert value2 != value1
    assert value2 == new_value


def test_write_float(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'float')
    value1 = float(field1.value)

    new_value = -555.0
    with MemoryView(process_info.pid, 'w') as view:
        view.write_float(new_value, field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'float')
    value2 = float(field2.value)

    assert field1.address == field2.address
    assert value2 != value1
    assert value2 == new_value


def test_write_double(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'double')
    value1 = float(field1.value)

    new_value = -555.0
    with MemoryView(process_info.pid, 'w') as view:
        view.write_double(new_value, field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'double')
    value2 = float(field2.value)

    assert field1.address == field2.address
    assert value2 != value1
    assert value2 == new_value


def test_write(write_test_process):
    process_info = next(write_test_process)

    field1 = next(v for v in process_info.values
                  if v.type == 'bytes')
    values1 = bytes([int(num) for num in field1.value.split()])

    new_values = bytes(range(len(values1)))
    with MemoryView(process_info.pid, 'w') as view:
        view.write(new_values, field1.address)

    field2 = next(v for v in next(write_test_process).values
                  if v.type == 'bytes')
    values2 = bytes([int(num) for num in field2.value.split()])

    assert field1.address == field2.address
    assert values2 != values1
    assert values2 == new_values
