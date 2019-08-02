"""Classes for SDMX messages.

The module implements classes that are NOT described in the SDMX Information
Model (SDMX-IM) spec, but are used in XML and JSON messages.
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
    error: Text = None
    id: Text = None
    prepared: Text = None
    receiver: Text = None
    sender: Union[Item, Text] = None

    def __repr__(self):
        """String representation."""
        lines = ['<Header>']
        lines.extend(_summarize(self, self.__fields__.keys()))
        return '\n  '.join(lines)


class Footer(BaseModel):
    severity: Text
    text: List[InternationalString] = []
    code: int


class Message(BaseModel):
    """Message."""
    class Config:
        # for .response
        arbitrary_types_allowed = True
        # NB this is required to prevent “unhashable type: 'dict'” in pydantic
        validate_assignment = False

    #: :class:`Header` instance.
    header: Header = Header()
    #: (optional) :class:`Footer` instance.
    footer: Footer = None
    #: :class:`requests.Response` instance.
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
    category_scheme: DictLike[str, CategoryScheme] = DictLike()
    codelist: DictLike[str, Codelist] = DictLike()
    concept_scheme: DictLike[str, ConceptScheme] = DictLike()
    constraint: DictLike[str, ContentConstraint] = DictLike()
    dataflow: DictLike[str, DataflowDefinition] = DictLike()
    structure: DictLike[str, DataStructureDefinition] = DictLike()
    organisation_scheme: DictLike[str, AgencyScheme] = DictLike()
    provisionagreement: DictLike[str, ProvisionAgreement] = DictLike()

    def __repr__(self):
        """String representation."""
        lines = [super().__repr__()]

        # StructureMessage contents
        for name in dir(self):
            attr = getattr(self, name)
            if not isinstance(attr, DictLike) or len(attr) == 0:
                continue
            lines.append(summarize_dictlike(attr))

        return '\n  '.join(lines)


class DataMessage(Message):
    #: :class:`list` of :class:`pandasdmx.model.DataSet`
    data: List[DataSet] = []
    dataflow: DataflowDefinition = DataflowDefinition()

    # TODO infer the observation dimension from the DSD, e.g.
    # - If a *TimeSeriesDataSet, it's the TimeDimension,
    # - etc.
    observation_dimension: Union[_AllDimensions, List[Dimension]] = None

    # Convenience access
    @property
    def structure(self):
        """The DataStructureDefinition used in the DataMessage.dataflow."""
        return self.dataflow.structure

    def __repr__(self):
        """String representation."""
        lines = [super().__repr__()]

        # DataMessage contents
        if len(self.data):
            lines.append('DataSet ({})'.format(len(self.data)))
        lines.extend(_summarize(self, ('dataflow', 'observation_dimension')))

        return '\n  '.join(lines)
