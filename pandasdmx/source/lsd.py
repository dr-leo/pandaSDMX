from . import Source as BaseSource


class Source(BaseSource):
    _id = "LSD"

    def handle_response(self, response, content):
        """LSD responses return a non-standard content-type."""
        content_type = response.headers.get("content-type", "")
        if "application/force-download" in content_type:
            response.headers["content-type"] = content_type.replace(
                "application/force-download", "application/xml"
            )
        return response, content
