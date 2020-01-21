"""Classes for SDMX messages.

:class:`Message` and related classes are not defined in the SDMX
:ref:`information model <im>`, but in the :ref:`SDMX-ML standard <formats>`.

pandaSDMX also uses :class:`DataMessage` to encapsulate SDMX-JSON data returned
by data sources.
"""
from typing import (
    List,
    Text,
    Union,
    )

from pandasdmx.model import (
    _AllDimensions,
    AgencyScheme,
    CategoryScheme,
    Codelist,
    ConceptScheme,
    ContentConstraint,
    DataSet,
    DataflowDefinition,
    DataStructureDefinition,
    Dimension,
    InternationalString,
    Item,
    ProvisionAgreement,
    )
from pandasdmx.util import BaseModel, DictLike, summarize_dictlike
from requests import Response


def _summarize(obj, fields):
    """Helper method for __repr__ on Header and Message (sub)classes."""
    for name in fields:
        attr = getattr(obj, name)
        if attr is None:
            continue
        yield f'{name}: {attr!r}'


class Header(BaseModel):
    """Header of an SDMX-ML message.

    SDMX-JSON messages do not have headers.
    """
    #: (optional) Error code for the message.
    error: Text = None
    #: Identifier for the message.
    id: Text = None
    #: Date and time at which the message was generated.
    prepared: Text = None
    #: Intended recipient of the message, e.g. the user's name for an
    #: authenticated service.
    receiver: Text = None
    #: The :class:`.Agency` associated with the data :class:`~.source.Source`.
    sender: Union[Item, Text] = None

    def __repr__(self):
        """String representation."""
        lines = ['<Header>']
        lines.extend(_summarize(self, self.__fields__.keys()))
        return '\n  '.join(lines)


class Footer(BaseModel):
    """Footer of an SDMX-ML message.

    SDMX-JSON messages do not have footers.
    """
    severity: Text
    #: The body text of the Footer contains zero or more blocks of text.
    text: List[InternationalString] = []
    code: int


class Message(BaseModel):
    class Config:
        # for .response
        arbitrary_types_allowed = True
        # NB this is required to prevent “unhashable type: 'dict'” in pydantic
        validate_assignment = False

    #: :class:`Header` instance.
    header: Header = Header()
    #: (optional) :class:`Footer` instance.
    footer: Footer = None
    #: :class:`requests.Response` instance for the response to the HTTP request
    #: that returned the Message. This is not part of the SDMX standard.
    response: Response = None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        """String representation."""
        lines = [
            f'<pandasdmx.{self.__class__.__name__}>',
            repr(self.header).replace('\n', '\n  '),
        ]
        lines.extend(_summarize(self, ['footer', 'response']))
        return '\n  '.join(lines)


class ErrorMessage(Message):
    pass


class StructureMessage(Message):
    #: Collection of :class:`.CategoryScheme`.
    category_scheme: DictLike[str, CategoryScheme] = DictLike()
    #: Collection of :class:`.Codelist`.
    codelist: DictLike[str, Codelist] = DictLike()
    #: Collection of :class:`.ConceptScheme`.
    concept_scheme: DictLike[str, ConceptScheme] = DictLike()
    #: Collection of :class:`.ContentConstraint`.
    constraint: DictLike[str, ContentConstraint] = DictLike()
    #: Collection of :class:`.DataflowDefinition`.
    dataflow: DictLike[str, DataflowDefinition] = DictLike()
    #: Collection of :class:`.DataStructureDefinition`.
    structure: DictLike[str, DataStructureDefinition] = DictLike()
    #: Collection of :class:`.AgencyScheme`.
    organisation_scheme: DictLike[str, AgencyScheme] = DictLike()
    #: Collection of :class:`.ProvisionAgreement`.
    provisionagreement: DictLike[str, ProvisionAgreement] = DictLike()

    def __repr__(self):
        """String representation."""
        lines = [super().__repr__()]

        # StructureMessage contents
        for attr in self.__dict__.values():
            if isinstance(attr, DictLike) and attr:
                lines.append(summarize_dictlike(attr))

        return '\n  '.join(lines)


class DataMessage(Message):
    """Data Message.

    .. note:: A DataMessage may contain zero or more :class:`.DataSet`, so
       :attr:`data` is a list. To retrieve the first (and possibly only)
       data set in the message, access the first element of the list:
       ``msg.data[0]``.
    """
    #: :class:`list` of :class:`.DataSet`.
    data: List[DataSet] = []
    #: :class:`.DataflowDefinition` that contains the data.
    dataflow: DataflowDefinition = DataflowDefinition()

    # TODO infer the observation dimension from the DSD, e.g.
    # - If a *TimeSeriesDataSet, it's the TimeDimension,
    # - etc.
    observation_dimension: Union[_AllDimensions, List[Dimension]] = None

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
            lines.append('DataSet ({})'.format(len(self.data)))
        lines.extend(_summarize(self, ('dataflow', 'observation_dimension')))

        return '\n  '.join(lines)
