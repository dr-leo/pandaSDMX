# encoding: utf-8

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Int 
import requests
from tempfile import SpooledTemporaryFile as STF
from io import BytesIO
import re, zipfile, time


    

class REST(LoggingConfigurable):
    """
    Query resources via REST
    """

    max_size = Int(2**24, config=True, 
                   help='max size of in-memory file before spooling to disk')
            
    def __init__(self):
        super(REST, self).__init__()
        self.name = 'pandasdmx.client.REST'
        
        
                             
    def get(self, url, from_file = None, params = {}):
        '''
        Read file from URL or local file.
        
        Return file-like for parsing
        Raise error if file could not be obtained.
 '''
        if from_file:
            # Load data from local file 
            source = open(from_file, 'rb')
            final_url = None    
        else:
            self.log.debug('Requesting %s', url)
            source, final_url = self.request(url, params = params) 
        return source, final_url
         
    
    def request(self, url, params = {}):
        """
        Retrieve SDMX messages.
        If needed, override in subclasses to support other data providers.

        :param url: The URL of the message.
        :type url: str
        :return: the xml data as file-like object 
        """
        
        response = requests.get(url, params = params, stream = True, timeout= 30.1)
        
        if response.status_code == requests.codes.OK:
            source  = STF(max_size = self.max_size)
            for c in response.iter_content(chunk_size = 1000000):
                source.write(c)
            source.seek(0)
        elif response.status_code == 430:
            #Sometimes, eurostat creates a zipfile when the query is too large. We have to wait for the file to be generated.
            parser = lxml.etree.XMLParser(
                                          ns_clean=True, recover=True)
            tree = lxml.etree.fromstring(source, parser = parser)
            messages = tree.xpath('.//footer:Message/common:Text',
                                      namespaces = tree.nsmap)
            regex_ = re.compile("Due to the large query the response will be written "
                                "to a file which will be located under URL: (.*)")
            matches = [regex_.match(element.text) for element in messages]
            if matches:
                source = None
                i = 30
                while i < 51:
                    time.sleep(i)
                    i = i+10
                    url = matches[0].groups()[0]
                    response = requests.get(url)
                    if response.headers['content-type'] == "application/octet-stream":
                        buffer = BytesIO(response.content)
                        file = zipfile.ZipFile(buffer)
                        filename = file.namelist()[0]
                        source = file.read(filename)
                        break
                if source is None:
                    raise requests.exceptions.HTTPError("The SDMX server didn't provide the requested file. Error code: {0}" 
                                                            .format(response.status_code))
            else:
                raise requests.exceptions.HTTPError(
                        "SDMX server returned an error message. Code: {0}"
                        .format(response.status_code))      
        else:
            raise requests.exceptions.HTTPError("SDMX server returned an error message. Code: {0}"
                    .format(response.status_code))      
        return source, response.url
