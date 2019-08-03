import pandasdmx as sdmx

from . import specimen


EXPECTED = {
    # Structure messages
    'insee-IPI-2010-A21-datastructure.xml': """<pandasdmx.StructureMessage>
  <Header>
    id: 'categorisation_1450864290565'
    prepared: '2015-12-23T09:51:30.565Z'
    receiver: 'unknown'
    sender: 'FR1'
  CategoryScheme (1): CLASSEMENT_DATAFLOWS
  Codelist (3): CL_FREQ CL_NAF2_A21 CL_NATURE
  ConceptScheme (1): CONCEPTS_INSEE
  DataflowDefinition (1): IPI-2010-A21
  DataStructureDefinition (1): IPI-2010-A21""",

    # This message shows the summarization feature: the DFD list is truncated
    'insee-dataflow.xml': """<pandasdmx.StructureMessage>
  <Header>
    id: 'dataflow_ENQ-CONJ-TRES-IND-PERSP_1450865196042'
    prepared: '2015-12-23T10:06:36.042Z'
    receiver: 'unknown'
    sender: 'FR1'
  DataflowDefinition (663): ACT-TRIM-ANC BPM6-CCAPITAL BPM6-CFINANCIER ...""",

    # Data message
    'ecb_exr_sg_xs.xml': """<pandasdmx.DataMessage>
  <Header>
    id: 'Generic'
    prepared: '2010-01-04T16:21:49+01:00'
    sender: 'ECB'
  DataSet (1)
  dataflow: <DataflowDefinition: 'STR1'=''>
  observation_dimension: [<Dimension: CURRENCY>]""",

    # This message has two DataSets:
    'exr-action-delete.json': """<pandasdmx.DataMessage>
  <Header>
    id: '62b5f19d-f1c9-495d-8446-a3661ed24753'
    prepared: '2012-11-29T08:40:26Z'
    sender: <Item: 'ECB'='European Central Bank'>
  DataSet (2)
  dataflow: <DataflowDefinition: 'None'=''>
  observation_dimension: [<Dimension: CURRENCY>]""",
}


def test_message_repr():
    for pattern, result in EXPECTED.items():
        with specimen(pattern) as f:
            msg = sdmx.read_sdmx(f)
        assert str(msg) == result
