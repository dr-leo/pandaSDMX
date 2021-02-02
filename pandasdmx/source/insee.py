from . import Source as BaseSource


class Source(BaseSource):
    _id = "INSEE"

    def modify_request_args(self, kwargs):
        """Supply explicit provider agency ID for INSEE.

        This web service accepts either "ALL" or "FR1" as a provider agency ID for
        structure endpoints, but not "INSEE" (see :issue:`21`).

        This hook sets the provider to "ALL" for structure queries if it is not given
        explicitly.
        """
        super().modify_request_args(kwargs)

        # NB this is an indirect test for resource_type != 'data'; because of
        #    the way the hook is called, resource_type is not available
        #    directly.
        if "key" not in kwargs:
            kwargs.setdefault("provider", "ALL")
