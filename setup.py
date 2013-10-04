#!/usr/bin/env python
import os
import sys
import ideal
from setuptools import setup, find_packages


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


readme = read_file('README.rst')
changes = read_file('CHANGES.rst')


install_requires = [
    'requests>=1.2.0',
    'lxml',
    'python-dateutil',
    'M2Crypto>=0.21'
]
tests_require = [
    'nose',
    'unittest2',
    'mock',
]


setup(
    name='ideal',
    version='.'.join(map(str, ideal.__version__)),
    license='MIT',

    # Packaging.
    packages=find_packages(exclude=('tests', 'tests.*')),
    install_requires=install_requires,
    dependency_links=[],
    tests_require=tests_require,
    include_package_data=True,
    zip_safe=False,

    # Metadata for PyPI.
    description='Python iDEAL v3.3.1+ implementation.',
    long_description='\n\n'.join([readme, changes]),
    author='Maykin Media, Joeri Bekker',
    author_email='joeri@maykinmedia.nl',
    platforms=['any'],
    url='http://github.com/maykinmedia/python-ideal',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development',
    ],
)
