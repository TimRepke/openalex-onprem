from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        'invert_index.pyx',
        language_level='3',
        annotate=False
    ),
)
