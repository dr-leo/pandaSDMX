from . import Source as BaseSource


class Source(BaseSource):
    _id = "SGR"

    def handle_response(self, response, content):
        """SGR responses do not specify content-type; set it directly."""
        if response.headers.get("content-type", None) is None:
            response.headers["content-type"] = "application/xml"
        return response, content

    def modify_request_args(self, kwargs):
        """SGR is a data source but not a data provider.

        Override the ``agency`` argument by setting ``agency='all'`` to
        retrieve all data republished by SGR from different providers.
        """
        super().modify_request_args(kwargs)

        kwargs.setdefault("provider", "all")
