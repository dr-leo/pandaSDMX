# encoding: utf-8

# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>, all rights reserved


from setuptools import setup
from codecs import open
# import re


# Get version
ver = '0.9.0'

# Publish README on PYPI when uploading.
long_descr = open('description.rst', 'r', encoding='utf8').read()

setup(name='pandaSDMX',
      version=ver,
      description='A client for SDMX - Statistical Data and Metadata eXchange',
      long_description=long_descr,
      author='Dr. Leo',
      author_email='fhaxbox66@gmail.com',
      packages=['pandasdmx'],
      package_data={'pandasdmx': ['agencies.json']},
      url='https://github.com/dr-leo/pandasdmx',
      install_requires=[
          'pandas',
          'lxml',
          'requests',
          'jsonpath-rw',
          'setuptools',
          'traitlets>=4.3',
          ],
      extras_require={
        'cache': ['requests_cache'],
        },
      tests_require=['odo', 'pytest-remotedata', 'requests-mock'],
      keywords='statistics SDMX pandas data economics science',
      zip_safe=True,
      provides=['pandasdmx'],
      classifiers=[
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Financial and Insurance Industry',
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Information Analysis'
          ]
      )
