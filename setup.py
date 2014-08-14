#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from distutils.core import setup
import os


# Publish README on PYPI when uploading.
# Need to expand it and rewrite it in reStructuredText 
long_descr = open('README.MD', 'r').read()

setup(name='pysdmx',
	version='0.1',
    description='A python interface to SDMX',
    long_description = long_descr,
    author='Widukind team',
    author_email='dev@michaelmalter.fr',
      py_modules=['sdmx'],
      url = 'https://github.com/widukind/pysdmx',
    requires=[
        'pandas',
        'lxml',
        'requests'
      ],
      provides = ['sdmx'],
      classifiers = [
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Financial and Insurance Industry',
         'Development Status :: 2 - Alpha',
        'License :: OSI Approved',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
'Programming Language :: Python :: 3.3',
'Programming Language :: Python :: 3.4',
                'Topic :: Scientific/Engineering',
                'Topic :: Scientific/Engineering :: Information Analysis'
    ]
    
	)
