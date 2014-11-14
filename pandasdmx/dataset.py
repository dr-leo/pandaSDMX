# encoding: utf-8

'''
Created on 15.10.2014


'''


from IPython.config.configurable import Configurable
from IPython.config.application import Application
from IPython.utils.traitlets import (
    Bool, Unicode, Int, Float, List, Dict
)


class Foo(Configurable):
    """A class that has configurable, typed attributes.

    """

    i = Int(0, config=True, help="The integer i.")
    j = Int(1, config=True, help="The integer j.")
    name = Unicode(u'Brian', config=True, help="First name.")


class Bar(Configurable):

    enabled = Bool(True, config=True, help="Enable bar.")


class Dataset(Application):

    name = Unicode(u'pandaSDMX')
    running = Bool(False, config=True,
                   help="Is the app running?")
    classes = List([pandasdmx.agency.Eurostat, pandasdmx.agency.ECB,
                    pandasdmx.client.BaseClient, pandasdmx.resource.Data21])
    config_file = Unicode(u'', config=True,
                   help="Load this config file")
    
    aliases = Dict(dict(i='Foo.i',j='Foo.j',name='Foo.name', running='MyApp.running',
                        enabled='Bar.enabled', log_level='MyApp.log_level'))
    
    flags = Dict(dict(enable=({'Bar': {'enabled' : True}}, "Enable Bar"),
                  disable=({'Bar': {'enabled' : False}}, "Disable Bar"),
                  debug=({'MyApp':{'log_level':10}}, "Set loglevel to DEBUG")
            ))
    
    def init_foo(self):
        # Pass config to other classes for them to inherit the config.
        self.foo = Foo(config=self.config)

    def init_bar(self):
        # Pass config to other classes for them to inherit the config.
        self.bar = Bar(config=self.config)

    def initialize(self, argv=None):
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)
        self.init_foo()
        self.init_bar()
    
    def start(self):
        print("app.config:")
        print(self.config)


def main():
    app = MyApp()
    app.initialize()
    app.start()


if __name__ == "__main__":
    main()
