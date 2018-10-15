from traitlets import All, HasTraits, Unicode, default


class MyClass(HasTraits):
    foo = Unicode()
    bar = Unicode()

    @default(All)
    def _maybe_read_default(self, proposal):
        print(self, proposal)


obj = MyClass()

obj.foo
