# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@uberdev.org>
# date: 2013/10/19
# copy: (C) Copyright 2013-EOT metagriffin -- see LICENSE.txt
#------------------------------------------------------------------------------
# This software is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------


class aadict(dict):

    '''
    A dict subclass that allows attribute access to be synonymous with
    item access, e.g. ``mydict.attribute == mydict['attribute']``. It
    also provides several other useful helper methods, such as
    :meth:`pick` and :meth:`omit`.
    '''

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            return object.__getattribute__(self, key)
    # def __setattr__(self, key, value):
    #  self[key] = value
    #  return self

    def __delattr__(self, key):
        if key in self:
            del self[key]
        return self

    def update(self, *args, **kw):
        args = [e for e in args if e]
        dict.update(self, *args, **kw)
        return self

    def pick(self, *args):
        return aadict({k: v for k, v in self.iteritems() if k in args})

    def omit(self, *args):
        return aadict({k: v for k, v in self.iteritems() if k not in args})

    @staticmethod
    def __dict2aadict__(subject, recursive=False):
        if isinstance(subject, list):
            if not recursive:
                return subject
            return [aadict.__dict2aadict__(val, True) for val in subject]
        if not isinstance(subject, dict):
            return subject
        ret = aadict(subject)
        if not recursive:
            return ret
        for key, val in ret.items():
            ret[key] = aadict.__dict2aadict__(val, True)
        return ret

    @staticmethod
    def d2ar(subject):
        return aadict.__dict2aadict__(subject, True)

    @staticmethod
    def d2a(subject):
        return aadict.__dict2aadict__(subject, False)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
