from . import Source as BaseSource


class Source(BaseSource):
    _id = "SGR"

    def handle_response(self, response, content):
        """SGR responses do not specify content-type; set it directly."""
        if response.headers.get("content-type", None) is None:
            response.headers["content-type"] = "application/xml"
        return response, content
