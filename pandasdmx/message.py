"""Classes for SDMX messages.

The module implements classes that are NOT described in the SDMX Information
Model (SDMX-IM) spec, but are used in XML and JSON messages.
"""
from typing import (
    List,
    Mapping,
    Optional,
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
    )
from pandasdmx.util import BaseModel, DictLike
from pydantic import validator
from requests import Response


class Header(BaseModel):
    error: Text = None
    id: Text = None
    prepared: Text = None
    receiver: Text = None
    sender: Union[Item, Text] = None


class Footer(BaseModel):
    severity: Text
    text: List[InternationalString] = []
    code: int


class Message(BaseModel):
    """Message."""
    class Config:
        arbitrary_types_allowed = True  # For Response
        validate_assignment = True

    #: :class:`Header` instance.
    header: Header = Header()
    #: (optional) :class:`Footer` instance.
    footer: Footer = None
    #: :class:`requests.Response` instance.
    response: Response = None


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
