from setuptools import find_packages, setup
from codecs import open


# Publish README on PYPI when uploading.
long_descr = open('description.rst', 'r', encoding='utf8').read()

TESTS_REQUIRE = [
    'odo>=0.5',
    'pytest>=3.3',
    'pytest-remotedata>=0.3.1',
    'requests-mock>=1.4',
    'requests>=2.7',
    ]

setup(name='pandaSDMX',
      version='1.0.0-dev',
      description='A client for SDMX - Statistical Data and Metadata eXchange',
      long_description=long_descr,
      author='Dr. Leo',
      author_email='fhaxbox66@gmail.com',
      packages=find_packages(),
      package_data={'pandasdmx': ['sources.json']},
      url='https://github.com/dr-leo/pandasdmx',
      install_requires=[
          'pandas>=0.20',
          'lxml>=3.6',
          'pydantic>=0.25',
          'requests',
          'setuptools>19',
          ],
      extras_require={
        'cache': ['requests_cache'],
        'docs': ['sphinx>=1.5'],
        'tests': TESTS_REQUIRE,
        },
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
