from setuptools import setup, Extension
import pybind11

functions_module = Extension(
    'bank_core', 
    sources=['bank_wrapper.cpp', 'bank_logic.cpp', 'sqlite3.c'], 
    include_dirs=[pybind11.get_include(), '.'],
    language='c++',
    extra_compile_args=['-std=c++11'],
    extra_link_args=['-static', '-static-libgcc', '-static-libstdc++'] 
)

setup(
    name='bank_core',
    version='1.0',
    ext_modules=[functions_module],
)