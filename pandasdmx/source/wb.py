from . import Source as BaseSource


class Source(BaseSource):
    _id = "WB"

    def modify_request_args(self, kwargs):
        """World Bank's agency ID."""
        super().modify_request_args(kwargs)

        kwargs.setdefault("provider", "WBG_WITS")
