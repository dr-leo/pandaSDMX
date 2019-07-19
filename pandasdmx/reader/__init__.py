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
    ctype = str(ctype).split(';')[0].strip()
    if ctype in ['application/xml',
                 'application/vnd.sdmx.genericdata+xml',
                 'application/vnd.sdmx.structure+xml',
                 'text/xml',
                 ]:
        from .sdmxml import Reader
        return Reader
    elif ctype in ['text/json']:
        from .sdmxjson import Reader
        return Reader
    else:
        raise ValueError(ctype)
