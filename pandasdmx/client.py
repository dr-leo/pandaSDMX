# encoding: utf-8

from IPython.config.configurable import Configurable 
import requests
from io import BytesIO
import re, zipfile, time




class BaseClient(Configurable):
    """
    Query resources via REST
    """
            
                     
    def get_source(self, url, to_file = None, from_file = None):
        '''
        Read file from URL or local file.
        Store the fetched string in a local file if specified to save download time next time.
        Return file-like for parsing
        Raise error if file could not be obtained.
 '''
        if from_file:
            # Load data from local file 
            source = open(from_file, 'rb')
                
        else:
            source = self.request(url) 
        
        if to_file:
            with open(to_file, 'wb') as f:
                f.write(source.read())
            source = to_file
            
        return source
         
    
    def request(self, url):
        """
        Retrieve SDMX messages.
        If needed, override in subclasses to support other data providers.

        :param url: The URL of the message.
        :type url: str
        :return: the xml data as file-like object 
        """
        
        response = requests.get(url, stream = True, timeout= 30.1)
        
        if response.status_code == requests.codes.ok:
            source  = response.raw 
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
        return source
