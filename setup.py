# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='redset',
    version='0.1.1',
    author='thekantian, jamesob',
    author_email='zach@percolate.com, jamesob@percolate.com',
    packages=['redset'],
    url='https://github.com/percolate/redset',
    license='see LICENSE',
    description='Simple, distributed sorted sets with redis',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
