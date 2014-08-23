# -*- coding: utf-8 -*-
from setuptools import setup

import redset

setup(
    name='redset',
    version=redset.__version__,
    author='thekantian, jamesob',
    author_email='zach@percolate.com, jamesob@percolate.com',
    packages=['redset'],
    url='https://github.com/percolate/redset',
    license='see LICENSE',
    description='Simple, distributed sorted sets with redis',
    long_description=open('README.rst').read(),
    tests_require=[
        'redis',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
