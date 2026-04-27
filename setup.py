import sys
from setuptools import setup, Extension
class get_pybind_include(object):
    def __str__(self):
        import pybind11
        return pybind11.get_include()
libs = []
link_args = []
if sys.platform.startswith('linux'):
    libs = ['pthread', 'dl']
elif sys.platform == 'win32':
    link_args = ['-static', '-static-libgcc', '-static-libstdc++']

functions_module = Extension(
    'bank_core', 
    sources=['bank_wrapper.cpp', 'bank_logic.cpp', 'sqlite3.c'], 
    include_dirs=[get_pybind_include(), '.'],
    libraries=libs,
    language='c++',
    extra_compile_args=['-std=c++11'],
    extra_link_args=link_args
)

setup(
    name='bank_core',
    version='1.0',
    ext_modules=[functions_module],
)
