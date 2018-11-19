# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
    This module contains the abstract base class for readers.

'''
from abc import ABC, abstractmethod


class BaseReader(ABC):
    @abstractmethod
    def read_message(self, source):
        """Read message from *source*.

        Must return an instance of a model.Message subclass.
        """
        pass  # pragma: no cover

    # Backwards-compatibility
    def initialize(self, source):
        return self.read_message(source)


def get_reader_for_content_type(ctype):
    ctype = ctype.split(';')[0]
    if ctype in ['text/xml',
                 'application/vnd.sdmx.genericdata+xml',
                 'application/vnd.sdmx.structure+xml']:
        from .sdmxml import Reader
        return Reader
    elif ctype in ['text/json']:
        from .sdmxjson import Reader
        return Reader
    else:
        raise ValueError(ctype)
