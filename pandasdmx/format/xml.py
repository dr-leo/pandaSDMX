import logging
from functools import lru_cache
from operator import itemgetter

from lxml.etree import QName

from pandasdmx import message, model

log = logging.getLogger(__name__)


# XML Namespaces
_base_ns = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1"
NS = {
    "": None,
    "com": f"{_base_ns}/common",
    "data": f"{_base_ns}/data/structurespecific",
    "str": f"{_base_ns}/structure",
    "mes": f"{_base_ns}/message",
    "gen": f"{_base_ns}/data/generic",
    "footer": f"{_base_ns}/message/footer",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


@lru_cache()
def qname(ns_or_name, name=None):
    """Return a fully-qualified tag *name* in namespace *ns*."""
    if isinstance(ns_or_name, QName):
        # Already a QName; do nothing
        return ns_or_name
    else:
        ns, name = ns_or_name.split(":") if name is None else (ns_or_name, name)
        return QName(NS[ns], name)


# Correspondence of message and model classes with XML tag names
_CLS_TAG = [
    (message.DataMessage, qname("mes:GenericData")),
    (message.DataMessage, qname("mes:GenericTimeSeriesData")),
    (message.DataMessage, qname("mes:StructureSpecificData")),
    (message.DataMessage, qname("mes:StructureSpecificTimeSeriesData")),
    (message.ErrorMessage, qname("mes:Error")),
    (message.StructureMessage, qname("mes:Structure")),
    (model.Agency, qname("str:Agency")),
    (model.Agency, qname("mes:Receiver")),
    (model.Agency, qname("mes:Sender")),
    (model.AttributeDescriptor, qname("str:AttributeList")),
    (model.Categorisation, qname("str:Categorisation")),
    (model.DataAttribute, qname("str:Attribute")),
    (model.DataflowDefinition, qname("str:Dataflow")),
    (model.DataStructureDefinition, qname("str:DataStructure")),
    (model.DataStructureDefinition, qname("com:Structure")),
    (model.DataStructureDefinition, qname("str:Structure")),
    (model.Dimension, qname("str:Dimension")),
    (model.Dimension, qname("str:DimensionReference")),
    (model.Dimension, qname("str:GroupDimension")),
    (model.DimensionDescriptor, qname("str:DimensionList")),
    (model.GroupDimensionDescriptor, qname("str:Group")),
    (model.GroupDimensionDescriptor, qname("str:AttachmentGroup")),
    (model.GroupKey, qname("gen:GroupKey")),
    (model.Key, qname("gen:ObsKey")),
    (model.MeasureDescriptor, qname("str:MeasureList")),
    (model.MeasureDimension, qname("str:MeasureDimension")),
    (model.SeriesKey, qname("gen:SeriesKey")),
    (model.StructureUsage, qname("com:StructureUsage")),
] + [
    (getattr(model, name), qname("str", name))
    for name in (
        "AgencyScheme",
        "Category",
        "CategoryScheme",
        "Code",
        "Codelist",
        "Concept",
        "ConceptScheme",
        "ContentConstraint",
        "DataProvider",
        "DataProviderScheme",
        "PrimaryMeasure",
        "TimeDimension",
    )
]


@lru_cache()
def class_for_tag(tag):
    """Return a message or model class for an XML tag."""
    results = map(itemgetter(0), filter(lambda ct: ct[1] == tag, _CLS_TAG))
    try:
        return next(results)
    except StopIteration:
        return None


@lru_cache()
def tag_for_class(cls):
    """Return an XML tag for a message or model class."""
    results = map(itemgetter(1), filter(lambda ct: ct[0] is cls, _CLS_TAG))
    try:
        return next(results)
    except StopIteration:
        return None
