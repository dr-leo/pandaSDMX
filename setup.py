from setuptools import find_packages, setup


INSTALL_REQUIRES = [
    'lxml>=3.6',
    'pandas>=0.20',
    'pydantic>=0.31',
    'requests>=2.7',
    'setuptools>19',
    ]

TESTS_REQUIRE = [
    'pytest>=3.3',
    'pytest-remotedata>=0.3.1',
    'requests-mock>=1.4',
    ]

EXTRAS_REQUIRE = {
    'cache': ['requests_cache'],
    'docs': ['sphinx>=1.5', 'ipython'],
    'tests': TESTS_REQUIRE,
    }

setup(name='pandaSDMX',
      version='1.0b1',
      description='A client for SDMX - Statistical Data and Metadata eXchange',
      author='pandaSDMX developers',
      author_email='fhaxbox66@gmail.com',
      packages=find_packages(),
      package_data={'pandasdmx': ['sources.json']},
      url='https://github.com/dr-leo/pandasdmx',
      install_requires=INSTALL_REQUIRES,
      extras_require=EXTRAS_REQUIRE,
      tests_require=TESTS_REQUIRE,
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
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.7',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Information Analysis'
          ]
      )
