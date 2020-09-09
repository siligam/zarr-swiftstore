# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import pathlib


here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding='utf-8')

setup(
    name='zarrswiftstore',
    version="1.1.1-beta",
    description='swift storage backend for zarr',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['zarrswift', 'zarrswift.tests'],
    install_requires=[
        'zarr',
        'python-swiftclient',
        'numcodecs>=0.6.4',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    author='Pavan Siligam',
    author_email='pavan.siligam@gmail.com',
    license='MIT',
    url="https://github.com/siligam/zarr-swiftstore",
    python_requires=">=3.6",
)
