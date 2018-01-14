from setuptools import find_packages, setup


def read_file(filename):
    with open(filename) as fl:
        return fl.read()


setup(
    name='memaccess',
    version='0.2',
    packages=find_packages(),
    author='Mischa Krüger (Makman2)',
    author_email='makmanx64@gmail.com',
    description="Python library for Windows giving live access to a program's memory",
    long_description=read_file('README.rst'),
    license='MIT',
    url='https://github.com/Makman2/memaccess',
)
