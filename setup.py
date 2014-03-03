#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from distutils.core import setup
import os

setup(name='pysdmx',
	version='0.1',
    description='A python interface to SDMX',
    author='Widukind team',
    author_email='dev@michaelmalter.fr',
      py_modules=['pysdmx'],
    install_requires=[
        'pandas>=0.12'
      ]
	)
