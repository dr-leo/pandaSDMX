from . import Source as BaseSource


class Source(BaseSource):
    _id = "ILO"

    def modify_request_args(self, kwargs):
        """Handle two limitations of ILO's REST service.

        1. Service returns SDMX-ML 2.0 by default, whereas :mod:`sdmx` only
           supports SDMX-ML 2.1. Set ``?format=generic_2_1`` query parameter.
        2. The service does not support values 'parents', 'parentsandsiblings'
           (the default), and 'all' for the ``references`` query parameter.
           Override the default with ``?references=none``.

           .. note:: Valid values are: none, parents, parentsandsiblings,
              children, descendants, all, or a specific structure reference
              such as 'codelist'.
        """
        super().modify_request_args(kwargs)

        kwargs.setdefault("params", {})
        kwargs["params"].setdefault("format", "generic_2_1")
        kwargs["params"].setdefault("references", "none")
