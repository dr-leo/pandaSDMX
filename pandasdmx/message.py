"""Classes for SDMX messages.

The module implements classes that are NOT described in the SDMX Information
Model (SDMX-IM) spec, but are used in XML and JSON messages.
"""
from traitlets import (
    CInt,
    HasTraits,
    Instance,
    List,
    Unicode,
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
from pandasdmx.util import DictLikeTrait
from requests import Response


class Header(HasTraits):
    error = Unicode()
    id = Unicode()
    prepared = Unicode()
    receiver = Unicode()
    sender = Union([Instance(Item), Unicode()])


class Footer(HasTraits):
    severity = Unicode()
    text = List(Instance(InternationalString))
    code = CInt()


class Message(HasTraits):
    """Message."""
    header = Instance(Header)
    footer = Instance(Footer, allow_none=True)
    response = Instance(Response)


class ErrorMessage(Message):
    pass


class StructureMessage(Message):
    category_scheme = DictLikeTrait(Instance(CategoryScheme))
    codelist = DictLikeTrait(Instance(Codelist))
    concept_scheme = DictLikeTrait(Instance(ConceptScheme))
    constraint = DictLikeTrait(Instance(ContentConstraint))
    dataflow = DictLikeTrait(Instance(DataflowDefinition))
    structure = DictLikeTrait(Instance(DataStructureDefinition))
    organisation_scheme = DictLikeTrait(Instance(AgencyScheme))


class DataMessage(Message):
    data = List(Instance(DataSet))
    dataflow = Instance(DataflowDefinition, args=())

    # TODO infer the observation dimension from the DSD, e.g.
    # - If a *TimeSeriesDataSet, it's the TimeDimension,
    # - etc.
    observation_dimension = Union([Instance(_AllDimensions),
                                   List(Instance(Dimension))], allow_none=True)

    # Convenience access
    @property
    def structure(self):
        """The DataStructureDefinition used in the DataMessage.dataflow."""
        return self.dataflow.structure
