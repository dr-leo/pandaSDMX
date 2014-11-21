# encoding: utf-8

'''
Created on 15.10.2014


'''
from IPython.config.configurable import Configurable 
from IPython.utils.traitlets import Instance
import sqlite3



class Storage(Configurable):
    '''
    Wrapper class for storage backends
    '''

    backend = Instance('Backend', config = True, help = """
    Path of the backend class. Currently there is only an SQLite3 backend.""")

    def __init__(self, params):
        super(Storage, self).__init__()
        
    def find(self, word):
        return Storage.backend.find(word)
    
                
class Backend(Configurable):
    """
    Base class for storage backends.
    """
    
    engine = Instance('object', config = True, help = 
                      """
                      class path of the storage engine, e.g. initialize function of a database.
                      """)
                    
    def __init__(self, *args, **kwargs):
        super(Backend, self).__init__()         
        
    def __del__(self):
        if Backend.engine: Backend.close()

    def close(self): 
        raise NotImplemented

    def find(self, word): 
        raise NotImplemented

class SQLite(Backend):
    """
    Backend class for SQLite
    """
    def __init__(self, *args, **qwargs):
        super(SQLite, self).__init__()
        self.db = sqlite3.SQLite
        
        
        
    def find(self, keyword):
        """
        Wrapper for SQL query in "SELECT * FROM <AgencyID>_dataflows
        WHERE title LIKE '%<keyword>%'")
        If dataflows have not been downloaded, get_dataflows method is called first.
        return search result as list of sqlite3.Row instances
        """
        name = self.agencyID + "_dataflows"
        if not self.db:
            self._init_database(name, delete_rows = False)
        # Is list of dataflows already in the database?
        cur = self.db.cursor()
        tables = cur.execute("SELECT * FROM SQLITE_MASTER")
        exists = [t for t in tables if t['name'] == name]
        # is it empty?
        if exists:
            first_row = cur.execute("SELECT * FROM {0}".format(name)).fetchone() 
        if not exists or not first_row: 
            self.get_dataflows()
        cur = self.db.execute(u"SELECT * FROM {0} WHERE title LIKE '%{1}%'"
        .format(name, keyword))
        return cur.fetchall()

    def _init_database(self, tablename, delete_rows = True):
        
        '''
        Helper method to initialize database.
        Called by get_dataflows()
        Return: sqlite3.Connection
        '''
        if not self.db:
            self.db = sqlite3.connect(self.db_filename)
            self.db.row_factory = sqlite3.Row
        self.db.execute(u'''CREATE TABLE IF NOT EXISTS {0} 
            (id INTEGER PRIMARY KEY, agencyID text, flowref text, version text, title text)'''.format( 
            tablename))
        # Delete any pre-existing rows
        if delete_rows:
            anyrows = self.db.execute('SELECT * FROM {0}'.format(
                tablename)).fetchone()
            if anyrows:
                self.db.execute('DELETE FROM {0}'.format(tablename))
        return self.db
        
