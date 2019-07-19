from requests import HTTPError  # noqa: F401


class ParseError(Exception):
    """:class:`pandasdmx.reader.Reader` is unable to parse a message."""
    pass


class XMLParseError(ParseError):
    """Error in parsing SDMX-ML.

    Parameters
    ----------
    reader : pandasdmx.reader.sdmxml.Reader
    elem : lxml.etree.Element
    """
    def __init__(self, reader, elem, message=None):
        self.stack = reader._stack
        self.elem = elem
        self.message = message
        self.__suppress_context__ = True

    def __str__(self):
        from lxml import etree

        msg = '\n\n'.join(filter(None, [
            self.message,
            '{}: {}'.format(self.__cause__.__class__.__name__,
                            self.__cause__),
            'Stack:\n' + '\n> '.join(self.stack),
            etree.tostring(self.elem, pretty_print=True).decode(),
            ]))
        self.__cause__ = None
        return msg
