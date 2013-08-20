# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='quedis',
    version='0.1',
    author='thekantian',
    author_email='zach@percolate.com',
    packages=['quedis'],
    url='https://github.com/percolate/quedis',
    license='see LICENCE.txt',
    description='A simple way to get use Redis sorted sets as task queues.',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
    ],
)
