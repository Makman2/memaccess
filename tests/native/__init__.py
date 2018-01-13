import os.path
from subprocess import check_call


def build_native_testapp(name):
    module_path = os.path.dirname(os.path.realpath(__file__))

    test_app_path = os.path.join(module_path, name)
    if not os.path.isdir(test_app_path):
        raise ValueError('No test directory for {} found'.format(name))

    build_directory = os.path.join(test_app_path, 'build')

    # Create necessary build directories.
    os.makedirs(build_directory, exist_ok=True)

    # Compile.
    check_call(('cmake', test_app_path), cwd=build_directory)
    check_call(('cmake', '--build', build_directory), cwd=build_directory)

    return os.path.join(build_directory, name)
