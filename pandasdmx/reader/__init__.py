# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
    This module contains the base class for readers.

'''


class BaseReader:

    def __init__(self, request, **kwargs):
        self.request = request

    def initialize(self, source):
        raise NotImplemented
