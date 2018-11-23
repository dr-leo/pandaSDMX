from . import Source as BaseSource


class Source(BaseSource):
    """SGR responses do not specify content-type."""
    _id = 'SGR'

    def handle_response(self, response, content):
        if response.headers.get('content-type', None) is None:
            response.headers['content-type'] = 'application/xml'
        return response, content
