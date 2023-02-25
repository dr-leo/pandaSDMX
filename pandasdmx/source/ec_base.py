"""
Base class for sources provided by the European Commission
"""


from . import Source as BaseSource
from pandasdmx.util import Resource
import logging

log = logging.getLogger(__name__)

class EC_BaseSource(BaseSource):
    """
    Suppress `references=ALL` param for metadata queries as the new API
    throws an error as of Feb. 2023.

    """

    _id = ""

    def modify_request_args(self, kwargs):
        super().modify_request_args(kwargs)
        resource_type = kwargs.get("resource_type")

        # Handle the ?references= query parameter
        params = kwargs.setdefault("params", {})
        references = params.get("references")
        if references is None:
            # Client._request_from_args() sets "all" or "parentsandsiblings" by default.
            # Neither of these values is supported by ESTAT; use "descendants" instead.
            if (
                resource_type
                in (Resource.categoryscheme, Resource.dataflow, Resource.datastructure)
                and kwargs.get("resource_id")
            ) or kwargs.get("resource"):
                params["references"] = "descendants"
        elif references not in ("children", "descendants", "none"):
            log.info(f"Replace unsupported references={references!r} with 'none'")
            params["references"] = "none"



