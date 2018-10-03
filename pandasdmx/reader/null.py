from pandasdmx.reader import BaseReader


class Reader(BaseReader):
    def __init__(self):
        # Don't require a Request object; pass None to the parent class
        super(Reader, self).__init__(None)

    def initialize(self):
        pass
