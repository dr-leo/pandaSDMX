from setuptools import find_packages, setup
from codecs import open


# Publish README on PYPI when uploading.
long_descr = open('description.rst', 'r', encoding='utf8').read()

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
          'pandas',
          'lxml',
          'pydantic',
          'requests',
          'jsonpath-rw',
          'setuptools',
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
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.7',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Information Analysis'
          ]
      )
