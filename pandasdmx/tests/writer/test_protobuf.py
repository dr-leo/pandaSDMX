import logging

import pytest

from pandasdmx.message import StructureMessage
from pandasdmx.writer.protobuf import write as to_protobuf


@pytest.mark.xfail(raises=RuntimeError, match="sdmx.format.protobuf_pb2 missing")
def test_codelist(caplog, codelist):
    """
    Prints a polynomial.

    Args:
        caplog: (todo): write your description
        codelist: (list): write your description
    """
    msg = StructureMessage()
    msg.codelist[codelist.id] = codelist

    caplog.set_level(logging.ERROR)

    result = to_protobuf(msg)

    print(result)

    # No errors logged
    assert len(caplog.messages) == 0
