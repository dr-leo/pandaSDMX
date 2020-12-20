"""Classes for SDMX messages.

:class:`Message` and related classes are not defined in the SDMX
:doc:`information model <implementation>`, but in the
:ref:`SDMX-ML standard <formats>`.

:mod:`pandasdmx` also uses :class:`DataMessage` to encapsulate SDMX-JSON data
returned by data sources.
"""
import logging
from datetime import datetime
from typing import List, Optional, Text, Union
from warnings import warn
from requests import Response

from pandasdmx import model
from pandasdmx.util import BaseModel, DictLike, compare, summarize_dictlike


log = logging.getLogger(__name__)


def _summarize(obj, fields):
    """Helper method for __repr__ on Header and Message (sub)classes."""
    for name in fields:
        attr = getattr(obj, name)
        if attr is None:
            continue
        elif isinstance(attr, datetime):
            attr = attr.isoformat()
        yield f"{name}: {repr(attr)}"


class Header(BaseModel):
    """Header of an SDMX-ML message.

    SDMX-JSON messages do not have headers.
    """

    #: (optional) Error code for the message.
    error: Optional[Text] = None
    #: Date and time at which the data was extracted.
    extracted: Optional[datetime] = None
    #: Identifier for the message.
    id: Optional[Text] = None
    #: Date and time at which the message was generated.
    prepared: Optional[datetime] = None
    #: Start of the time period covered by a :class:`.DataMessage`.
    reporting_begin: Optional[datetime] = None
    #: End of the time period covered by a :class:`.DataMessage`.
    reporting_end: Optional[datetime] = None
    #: Intended recipient of the message, e.g. the user's name for an
    #: authenticated service.
    receiver: Optional[model.Agency] = None
    #: The :class:`.Agency` associated with the data :class:`~.source.Source`.
    sender: Optional[model.Agency] = None
    #:
    source: model.InternationalString = model.InternationalString()
    #:
    test: bool = False

    def __repr__(self):
        """String representation."""
        lines = ["<Header>"]
        lines.extend(_summarize(self, self.__fields__.keys()))
        return "\n  ".join(lines)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two Headers are the same if their corresponding attributes are equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return all(
            compare(attr, self, other, strict)
            for attr in [
                "error",
                "extracted",
                "id",
                "prepared",
                "reporting_begin",
                "reporting_end",
                "receiver",
                "sender",
                "source",
                "test",
            ]
        )


class Footer(BaseModel):
    """Footer of an SDMX-ML message.

    SDMX-JSON messages do not have footers.
    """

    #:
    severity: Optional[str] = None
    #: The body text of the Footer contains zero or more blocks of text.
    text: List[model.InternationalString] = []
    #:
    code: Optional[int] = None

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two Footers are the same if their :attr:`code`, :attr:`severity`, and
        :attr:`text` are equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return all(
            compare(attr, self, other, strict) for attr in ["severity", "text", "code"]
        )


class Message(BaseModel):
    class Config:
        # for .response
        arbitrary_types_allowed = True

    #: :class:`Header` instance.
    header: Header = Header()
    #: (optional) :class:`Footer` instance.
    footer: Optional[Footer] = None
    #: :class:`requests.Response` instance for the response to the HTTP request
    #: that returned the Message. This is not part of the SDMX standard.
    response: Optional[Response] = None

    def to_pandas(self, *args, **kwargs):
        """Convert a Message instance to :mod:`pandas` object(s).

        :func:`pandasdmx.writer.write` is called and passed
        the `Message` instance  as first argument, followed  by any `args` and `kwargs`.

        .. seealso:: :meth:`write`
        """
        from . import writer

        return writer.to_pandas(self, *args, **kwargs)

    def write(self, *args, **kwargs):
        """Alias for `to_pandas` improving backwards compatibility.

        .. deprecated:: 1.0
            Use :meth:`to_pandas` instead.
        """
        warn(
            "Message.write() is deprecated. Use Message.to_pandas() instead.",
            DeprecationWarning,
        )
        return self.to_pandas(*args, **kwargs)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        """String representation."""
        lines = [
            f"<pandasdmx.{self.__class__.__name__}>",
            repr(self.header).replace("\n", "\n  "),
        ]
        lines.extend(_summarize(self, ["footer", "response"]))
        return "\n  ".join(lines)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two Messages are the same if their :attr:`header` and :attr:`footer` compare
        equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return self.header.compare(other.header, strict) and (
            self.footer is other.footer is None
            or self.footer.compare(other.footer, strict)
        )


class ErrorMessage(Message):
    pass


class StructureMessage(Message):
    #: Collection of :class:`.Categorisation`.
    categorisation: DictLike[str, model.Categorisation] = DictLike()
    #: Collection of :class:`.CategoryScheme`.
    category_scheme: DictLike[str, model.CategoryScheme] = DictLike()
    #: Collection of :class:`.Codelist`.
    codelist: DictLike[str, model.Codelist] = DictLike()
    #: Collection of :class:`.ConceptScheme`.
    concept_scheme: DictLike[str, model.ConceptScheme] = DictLike()
    #: Collection of :class:`.ContentConstraint`.
    constraint: DictLike[str, model.ContentConstraint] = DictLike()
    #: Collection of :class:`.DataflowDefinition`.
    dataflow: DictLike[str, model.DataflowDefinition] = DictLike()
    #: Collection of :class:`.DataStructureDefinition`.
    structure: DictLike[str, model.DataStructureDefinition] = DictLike()
    #: Collection of :class:`.AgencyScheme`.
    organisation_scheme: DictLike[str, model.AgencyScheme] = DictLike()
    #: Collection of :class:`.ProvisionAgreement`.
    provisionagreement: DictLike[str, model.ProvisionAgreement] = DictLike()

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two StructureMessages compare equal if :meth:`.DictLike.compare` is :obj:`True`
        for each of the object collection attributes.

        Parameters
        ----------
        strict : bool, optional
            Passed to :meth:`.DictLike.compare`.
        """
        return super().compare(other, strict) and all(
            getattr(self, attr).compare(getattr(other, attr), strict)
            for attr in (
                "categorisation",
                "category_scheme",
                "codelist",
                "concept_scheme",
                "constraint",
                "dataflow",
                "structure",
                "organisation_scheme",
                "provisionagreement",
            )
        )

    def __repr__(self):
        """String representation."""
        lines = [super().__repr__()]

        # StructureMessage contents
        for attr in self.__dict__.values():
            if isinstance(attr, DictLike) and attr:
                lines.append(summarize_dictlike(attr))

        return "\n  ".join(lines)


class DataMessage(Message):
    """Data Message.

    .. note:: A DataMessage may contain zero or more :class:`.DataSet`, so
       :attr:`data` is a list. To retrieve the first (and possibly only)
       data set in the message, access the first element of the list:
       ``msg.data[0]``.
    """

    #: :class:`list` of :class:`.DataSet`.
    data: List[model.DataSet] = []
    #: :class:`.DataflowDefinition` that contains the data.
    dataflow: model.DataflowDefinition = model.DataflowDefinition()
    #: The "dimension at observation level".
    observation_dimension: Optional[
        Union[
            model._AllDimensions,
            model.DimensionComponent,
            List[model.DimensionComponent],
        ]
    ] = None

    # Convenience access
    @property
    def structure(self):
        """DataStructureDefinition used in the :attr:`dataflow`."""
        return self.dataflow.structure

    def __repr__(self):
        """String representation."""
        lines = [super().__repr__()]

        # DataMessage contents
        if self.data:
            lines.append("DataSet ({})".format(len(self.data)))
        lines.extend(_summarize(self, ("dataflow", "observation_dimension")))

        return "\n  ".join(lines)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two DataMessages are the same if:

        - :meth:`.Message.compare` is :obj:`True`
        - their :attr:`dataflow` and :attr:`observation_dimension` compare equal.
        - they have the same number of :class:`DataSets <DataSet>`, and
        - corresponding DataSets compare equal (see :meth:`.DataSet.compare`).

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return (
            super().compare(other, strict)
            and compare("dataflow", self, other, strict)
            and compare("observation_dimension", self, other, strict)
            and len(self.data) == len(other.data)
            and all(ds[0].compare(ds[1], strict) for ds in zip(self.data, other.data))
        )
