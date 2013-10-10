# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='redset',
    version='0.2.3',
    author='thekantian, jamesob',
    author_email='zach@percolate.com, jamesob@percolate.com',
    packages=['redset'],
    url='https://github.com/percolate/redset',
    license='see LICENSE',
    description='Simple, distributed sorted sets with redis',
    long_description=open('README.rst').read(),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
