from tempfile import NamedTemporaryFile
from time import sleep
from urllib.parse import urlparse
from zipfile import ZipFile

import requests

from . import Source as BaseSource


class Source(BaseSource):
    """Handle Eurostat's mechanism for large datasets.

    For some requests, ESTAT returns a DataMessage that has no content except
    for a ``<footer:Footer>`` element containing a URL where the data will be
    made available as a ZIP file.

    To configure :meth:`finish_message`, pass its `get_footer_url` argument to
    :meth:`.Request.get`.

    .. versionadded:: 0.2.1

    """

    _id = "ESTAT"

    def modify_request_args(self, kwargs):
        super().modify_request_args(kwargs)

        kwargs.pop("get_footer_url", None)

    def finish_message(self, message, request, get_footer_url=(30, 3), **kwargs):
        """Handle the initial response.

        This hook identifies the URL in the footer of the initial response,
        makes a second request (polling as indicated by *get_footer_url*), and
        returns a new DataMessage with the parsed content.

        Parameters
        ----------
        get_footer_url : (int, int)
            Tuple of the form (`seconds`, `attempts`), controlling the interval
            between attempts to retrieve the data from the URL, and the
            maximum number of attempts to make.
        """
        # Check the message footer for a text element that is a valid URL
        url = None
        for text in getattr(message.footer, "text", []):
            if urlparse(str(text)).scheme:
                url = str(text)
                break

        if not url:
            return message

        # Unpack arguments
        wait_seconds, attempts = get_footer_url

        # Create a temporary file to store the ZIP response
        ntf = NamedTemporaryFile(prefix="pandasdmx-")
        # Make a limited number of attempts to retrieve the file
        for a in range(attempts):
            sleep(wait_seconds)
            try:
                # This line succeeds if the file exists; the ZIP response
                # is stored to ntf, and then used by the
                # handle_response() hook below
                return request.get(url=url, tofile=ntf)
            except requests.HTTPError:
                raise
        ntf.close()
        raise RuntimeError("Maximum attempts exceeded")

    def handle_response(self, response, content):
        """Handle the polled response.

        The request for the indicated ZIP file URL returns an octet-stream;
        this handler saves it, opens it, and returns the content of the single
        contained XML file.

        """

        if response.headers["content-type"] != "application/octet-stream":
            return response, content

        # Read all the input, forcing it to be copied to
        # content.tee_filename
        while True:
            if len(content.read()) == 0:
                break

        # Open the zip archive
        with ZipFile(content.tee, mode="r") as zf:
            # The archive should contain only one file
            infolist = zf.infolist()
            assert len(infolist) == 1

            # Set the new content type
            response.headers["content-type"] = "application/xml"

            # Use the unzipped archive member as the response content
            return response, zf.open(infolist[0])
