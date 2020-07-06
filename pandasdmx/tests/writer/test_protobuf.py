import logging

import pytest

from sdmx.message import StructureMessage
from sdmx.writer.protobuf import write as to_protobuf


@pytest.mark.xfail(raises=RuntimeError, match="sdmx.format.protobuf_pb2 missing")
def test_codelist(caplog, codelist):
    msg = StructureMessage()
    msg.codelist[codelist.id] = codelist

    caplog.set_level(logging.ERROR)

    result = to_protobuf(msg)

    print(result)

    # No errors logged
    assert len(caplog.messages) == 0
