# encoding: utf-8

'''
.. module:: pandasdmx.application
    
    :synopsis: A Python- and pandas-powered client for statistical data and metadata exchange 
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; largely inspired by IPython's config system
'''


from IPython.config.configurable import Configurable
from IPython.config.application import Application
from IPython.utils.traitlets import (
    Bool, Unicode, Int, Float, List, Dict
)



class PandaSDMXApp(Application):

    name = Unicode(u'PandaSDMX')
    
    classes = List(['pandasdmx.agency.ECB', 'pandasdmx.agency.Eurostat'])
    
    log_level = 'DEBUG'
    
    config_file = Unicode(u'', config=True,
                   help="Load this config file")
    
    flags = Dict(dict(
                  debug=({'PandaSDMXApp':{'log_level':10}}, "Set loglevel to DEBUG")
            ))

    pandasdmx_dir = Unicode(config=True,
        help="""
        The name of the PandaSDMX directory. This directory is used for logging
        configuration etc. The default
        is usually $HOME/.pandasdmx. 
        """
    )
    def _pandasdmx_dir_default(self):
        d = get_pandasdmx_dir()
        self._pandasdmx_dir_changed('pandasdmx_dir', d, d)
        return d
    
    
    def initialize(self, argv=None):
        # self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)
        


app = PandaSDMXApp()
app.initialize()
