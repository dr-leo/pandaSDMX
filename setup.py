#! /usr/bin/env python3
# -*- coding: utf-8 -*-


from setuptools import setup
from codecs import open


# Publish README on PYPI when uploading.
# Need to expand it and rewrite it in reStructuredText 
long_descr = open('README.rst', 'r').read()

setup(name='PySDMX',
	version='0.1',
    description='A client for statistical data and metadata exchange based on pandas and SQLite',
    long_description = long_descr,
    author='Dr. Leo',
    author_email='fhaxbox66@gmail.com',
      py_modules=['sdmx'],
      url = 'https://github.com/widukind/pysdmx',
    install_requires=[
        'pandas',
        'lxml',
        'requests'
      ],
      provides = ['sdmx'],
      classifiers = [
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
       'Intended Audience :: Financial and Insurance Industry',
         'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
'Programming Language :: Python :: 3.3',
'Programming Language :: Python :: 3.4',
                'Topic :: Scientific/Engineering',
                'Topic :: Scientific/Engineering :: Information Analysis'
    ]
    
	)
