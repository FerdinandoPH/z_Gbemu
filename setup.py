from setuptools import setup
from Cython.Build import cythonize
setup(name="z_GBEMU", ext_modules=cythonize("Cpu.pyx"))