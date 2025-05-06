from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import platform

extra_compile_args = ["-O3"]

if platform.system() == "Darwin" and platform.machine() == "arm64":
    extra_compile_args.extend(["-ffast-math"])
else:
    extra_compile_args.extend(["-march=native", "-ffast-math"])

extensions = [
    Extension(
        "similarity_calculator",
        ["similarity_calculator.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=extra_compile_args,
    )
]

setup(
    name="similarity_calculator",
    ext_modules=cythonize(extensions, language_level=3),
    zip_safe=False,
)