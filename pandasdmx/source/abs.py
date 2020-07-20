import re

from . import Source as BaseSource

re_500 = re.compile(r"(An error has occurred)\.")


class Source(BaseSource):
    _id = "ABS"

    def handle_response(self, response, content):
        """Handle ABS' own text/html error page for some endpoints."""
        ctype = response.headers.get("content-type", "")
        if "text/html" in ctype:
            buf = ""
            while True:
                chunk = content.read().decode()
                if len(chunk) == 0:
                    break

                buf += chunk

                match = re_500.search(buf)
                if match:
                    # Overwrite the original response
                    (response.reason,) = match.groups()
                    response.status_code = 500
                    response.raise_for_status()

        raise NotImplementedError
