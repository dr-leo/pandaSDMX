from . import Source as BaseSource


class Source(BaseSource):
    _id = "ISTAT"

    def modify_request_args(self, kwargs):
        """Supply explicit provider agency ID for ISTAT.

        As reported by @guglielmo, https://github.com/dr-leo/pandaSDMX/pull/75,
        ISTAT requires a provider agency ID for structure endpoints. Values
        'IT1' and 'all' are known to work; we use 'all' to (hopefully) be
        inclusive of 'IT1' and any others.
        """
        super().modify_request_args(kwargs)

        # NB this is an indirect test for resource_type != 'data'; because of
        #    the way the hook is called, resource_type is not available
        #    directly.
        if "key" not in kwargs:
            kwargs.setdefault("provider", "all")
