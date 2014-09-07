#! /usr/bin/env python3
# -*- coding: utf-8 -*-


from setuptools import setup
from codecs import open


# Publish README on PYPI when uploading.
long_descr = open('description.rst', 'r').read()

setup(name='pandaSDMX',
	version='0.1',
    description='A Python- and pandas-powered client for statistical data and metadata exchange',
    long_description = long_descr,
    author='Dr. Leo',
    author_email='fhaxbox66@gmail.com',
      py_modules=['pandasdmx'],
      url = 'https://github.com/dr-leo/pandasdmx',
    install_requires=[
        'pandas',
        'lxml',
        'requests'
      ],
      provides = ['pandasdmx'],
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
