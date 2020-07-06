import re
from operator import itemgetter

import pytest

import sdmx

from .data import specimen

EXPECTED = [
    # Structure messages
    (
        "IPI-2010-A21-structure.xml",
        """<sdmx.StructureMessage>
  <Header>
    id: 'categorisation_1450864290565'
    prepared: '2015-12-23T09:51:30.565Z'
    receiver: <Agency unknown>
    sender: <Agency FR1: Institut national de la statistique et des études économiques>
    source: fr: Banque de données macro-économiques
    test: False
  Categorisation (1): CAT_IPI-2010_IPI-2010-A21
  CategoryScheme (1): CLASSEMENT_DATAFLOWS
  Codelist (7): CL_FREQ CL_NAF2_A21 CL_NATURE CL_UNIT CL_AREA CL_TIME_C...
  ConceptScheme (1): CONCEPTS_INSEE
  DataflowDefinition (1): IPI-2010-A21
  DataStructureDefinition (1): IPI-2010-A21""",
    ),
    (
        # This message shows the summarization feature: the DFD list is truncated
        "dataflow.xml",
        """<sdmx.StructureMessage>
  <Header>
    id: 'dataflow_ENQ-CONJ-TRES-IND-PERSP_1450865196042'
    prepared: '2015-12-23T10:06:36.042Z'
    receiver: <Agency unknown>
    sender: <Agency FR1: Institut national de la statistique et des études économiques>
    source: fr: Banque de données macro-économiques
    test: False
  DataflowDefinition (663): ACT-TRIM-ANC BPM6-CCAPITAL BPM6-CFINANCIER ...
  DataStructureDefinition (663): ACT-TRIM-ANC BPM6-CCAPITAL BPM6-CFINAN...""",
    ),
    # Data messages
    (
        "sg-xs.xml",
        """<sdmx.DataMessage>
  <Header>
    id: 'Generic'
    prepared: '2010-01-04T16:21:49+01:00'
    sender: <Agency ECB>
    source: """
        """
    test: False
  DataSet (1)
  dataflow: <DataflowDefinition (missing id)>
  observation_dimension: <Dimension CURRENCY>""",
    ),
    (
        # This message has two DataSets:
        "action-delete.json",
        """<sdmx.DataMessage>
  <Header>
    id: '62b5f19d-f1c9-495d-8446-a3661ed24753'
    prepared: '2012-11-29T08:40:26Z'
    sender: <Agency ECB: European Central Bank>
    source: """
        """
    test: False
  DataSet (2)
  dataflow: <DataflowDefinition (missing id)>
  observation_dimension: [<Dimension CURRENCY>]""",
    ),
]


@pytest.mark.parametrize(
    "pattern, expected", EXPECTED, ids=list(map(itemgetter(0), EXPECTED))
)
def test_message_repr(pattern, expected):
    with specimen(pattern) as f:
        msg = sdmx.read_sdmx(f)
    if isinstance(expected, re.Pattern):
        assert expected.fullmatch(repr(msg))
    else:
        assert expected == repr(msg)
