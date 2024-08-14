from setuptools import setup, find_packages

setup(
    name='polar_patch',
    version='0.1.0',
    description='A tool that brings type safety and type checking enhancements to the Polars library.',
    author='Stephen Oketch',
    author_email='oketchs702@gmail.com',
    packages=find_packages(include=['polar_patch', 'tests']),
    package_dir={'': '.'},
    url='https://github.com/Phronetic-Horizons/polar_patch',
    include_package_data=True,
)