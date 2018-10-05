from pandasdmx.reader import BaseReader


class Reader(BaseReader):
    def __init__(self):
        # Don't require a Request object; pass None to the parent class
        super(Reader, self).__init__(None)

    # Abstract methods of BaseReader
    def initialize(self):
        pass

    # Methods required by model.DataSet
    def dataset_attrib(self, sdmxobj):
        pass

    def iter_generic_obs(self, sdmxobj):
        pass

    def generic_series(self, sdmxobj):
        pass

    # Methods required by model.header
    def dim_at_obs(self, sdmxobj):
        pass

    def structured_by(self, sdmxobj):
        pass
