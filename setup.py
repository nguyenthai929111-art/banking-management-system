from setuptools import setup, Extension

class get_pybind_include(object):
    def __str__(self):
        import pybind11
        return pybind11.get_include()

functions_module = Extension(
    'bank_core', 
    sources=['bank_wrapper.cpp', 'bank_logic.cpp', 'sqlite3.c'], 
    include_dirs=[pybind11.get_include(), '.'],
    language='c++',
    extra_compile_args=['-std=c++11'],
)

setup(
    name='bank_core',
    version='1.0',
    ext_modules=[functions_module],
)
