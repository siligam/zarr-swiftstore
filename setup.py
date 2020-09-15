# -*- coding: utf-8 -*-

from setuptools import setup
import pathlib


here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding='utf-8')

setup(
    name='zarr-swiftstore',
    version="1.2.0",
    description='swift storage backend for zarr',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires=">=3.5",
    package_dir={'': '.'},
    packages=['zarrswift', 'zarrswift.tests'],
    install_requires=[
        'zarr>=2.4.0',
        'python-swiftclient>=3.10.0',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    author='Pavan Siligam',
    author_email='pavan.siligam@gmail.com',
    license='MIT',
    url="https://github.com/siligam/zarr-swiftstore",
)
