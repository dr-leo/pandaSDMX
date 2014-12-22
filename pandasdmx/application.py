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
import logging


class PandaSDMXApp(Application):

    name = Unicode(u'PandaSDMX')
    
    classes = List(['pandasdmx.agency.ECB', 'pandasdmx.agency.Eurostat'])
    
    
    
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
    
    
    def start_logger(self):
        """Copied from IPython.config.application with minor tweaks.

        The default is to log to stderr using a StreamHandler, if no default
        handler already exists.  The log level starts at logging.WARN, but this
        can be adjusted by setting the ``log_level`` attribute.
        """
        log = logging.getLogger(self.__class__.__name__)
        log.setLevel(self.log_level)
        log.propagate = False
        _log = log # copied from Logger.hasHandlers() (new in Python 3.2)
        while _log:
            if _log.handlers:
                return log
            if not _log.propagate:
                break
            else:
                _log = _log.parent
        if sys.executable.endswith('pythonw.exe'):
            # this should really go to a file, but file-logging is only
            # hooked up in parallel applications
            _log_handler = logging.StreamHandler(open(os.devnull, 'w'))
        else:
            _log_handler = logging.StreamHandler()
        _log_formatter = LevelFormatter(self.log_format, datefmt=self.log_datefmt)
        _log_handler.setFormatter(_log_formatter)
        log.addHandler(_log_handler)
        return log


    
    def initialize(self, argv=None):
        # self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)
        self.log_level = 'DEBUG'
        self.log = self.start_logger()
        


app = PandaSDMXApp()
app.initialize()
