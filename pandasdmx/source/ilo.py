import logging

from . import Source as BaseSource

log = logging.getLogger(__name__)


class Source(BaseSource):
    _id = "ILO"

    def modify_request_args(self, kwargs):
        """Handle limitations of ILO's REST service.

        1. Service returns SDMX-ML 2.0 by default, whereas :mod:`sdmx` only supports
           SDMX-ML 2.1. Set ``?format=generic_2_1`` query parameter.
        2. Service does not support the ``?references=…`` query parameter; discard.
        """
        super().modify_request_args(kwargs)

        kwargs.setdefault("params", {})
        kwargs["params"].setdefault("format", "generic_2_1")

        references = kwargs["params"].pop("references", None)
        if references:
            log.warning(
                f"{self.id} does not support references={references!r}; discarded"
            )
