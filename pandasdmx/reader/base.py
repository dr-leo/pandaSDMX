from pathlib import Path

try:
    import appdirs
except ImportError:
    pass

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List

from pandasdmx.util import parse_content_type

log = logging.getLogger(__name__)


class BaseReader(ABC):
    #: List of HTTP content types handled by the reader.
    content_types: List[str] = []

    #: List of file name suffixes handled by the reader.
    suffixes: List[str] = []

    @classmethod
    def detect(cls, content: bytes) -> bool:
        """Detect whether the reader can handle `content`.

        Returns
        -------
        bool
            :obj:`True` if the reader can handle the content.
        """
        return False

    @classmethod
    @lru_cache()
    def supports_content_type(cls, value: str) -> bool:
        """:obj:`True` if the reader can handle content/media type `value`."""
        other = parse_content_type(value)
        for ctype in map(parse_content_type, cls.content_types):
            if ctype[0] == other[0]:
                if ctype[1] != other[1]:
                    log.debug(
                        f"Match {ctype[0]} with params {other[1]}; expected {ctype[1]}"
                    )
                return True
        return False

    @classmethod
    def supports_suffix(cls, value: str) -> bool:
        """:obj:`True` if the reader can handle files with suffix `value`."""
        return value.lower() in cls.suffixes

    @abstractmethod
    def read_message(self, source, dsd=None):
        """Read message from *source*.

        Parameters
        ----------
        source : file-like
            Message content.
        dsd : DataStructureDefinition, optional
            DSD for aid in reading `source`.

        Returns
        -------
        :class:`.Message`
            An instance of a Message subclass.
        """
        pass  # pragma: no cover

    @staticmethod
    def get_schema_dir():
        return Path(appdirs.user_data_dir(appname="pandasdmx", appauthor=False))

    @staticmethod
    def validate_message(msg, schema_dir=None):
        raise NotImplementedError
