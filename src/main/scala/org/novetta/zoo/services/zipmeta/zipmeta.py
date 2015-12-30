# imports for tornado
import tornado
import tornado.web
import tornado.httpserver
import tornado.ioloop

# imports for logging
import traceback
import os
from os import path

# get ZipParser
import ZipParser
ZipParser = ZipParser.ZipParser

class ZipError (Exception):
    def __init__ (self, status, error):
        self.status = status
        self.error  = error
    def __str__ (self):
        return str(self.status) + " - " + str(self.error)
    def __repr__ (self):
        return repr(str(self))


class ResultSet (object):
    
    def __init__(self):
        self.data = {}
    
    def add(self, key, value):
        if key in self.data:
            if isinstance(self.data[key], list):
                self.data[key].append(value)
            else:
                cpy = self.data[key]
                self.data[key] = []
                self.data[key].append(cpy)
                self.data[key].append(value)
        else:
            self.data[key] = value


class ZipMetaProcess(tornado.web.RequestHandler):
    def get(self, filename):
        resultset = ResultSet()
        try:
            # read file
            fullPath = os.path.join('/tmp/', filename)
            with open(fullPath) as file:
                data = file.read()
            
            # exclude non-zip
            if len(data) < 4:
                raise ZipError(400, "Not enough filedata.")
            if data[:4] not in [ZipParser.zipLDMagic, ZipParser.zipCDMagic]:
                raise ZipError(400, "Not a zip file.")
            
            # parse
            parser    = ZipParser(data)
            parsedZip = parser.parseZipFile()
            if not parsedZip:
                raise ZipError(400, "Could not parse file as a zip file")
            
            # fetch result
            for centralDirectory in parsedZip:
                zipfilename = centralDirectory["ZipFileName"]
                zipentry = ResultSet()
                
                for name, value in centralDirectory.iteritems():
                    if name == 'ZipExtraField':
                        continue
                    
                    if type(value) is list or type(value) is tuple:
                        for element in value:
                            zipentry.add(name, str(element))
                    
                    # Add way to handle dictionary.
                    #if type(value) is dict: ...
                    else:
                        zipentry.add(name, str(value))
                    
                if centralDirectory["ZipExtraField"]:
                    for dictionary in centralDirectory["ZipExtraField"]:
                        zipextra = ResultSet()
                        if dictionary["Name"] == "UnknownHeader":
                            for name, value in dictionary.iteritems():
                                if name == "Data":
                                    value = "Data"
                                zipextra.add(name, str(value))
                        else:
                            for name, value in dictionary.iteritems():
                                zipextra.add(name, str(value))
                        zipentry.add(dictionary["Name"], zipextra.data)
                else:
                    zipentry.add("ZipExtraField", "None")
                
                resultset.add(zipfilename, zipentry.data)
            
            self.write({"files": resultset.data})
        
        except ZipError as ze:
            self.set_status(ze.status, str(ze.error))
            self.write("")
        except Exception as e:
            self.set_status(500, "Unknown error happened")
            self.write({"error": traceback.format_exc(e)})


class Info(tornado.web.RequestHandler):
    # Emits a string which describes the purpose of the analytics
    def get(self):
        description = """
<p>Copyright 2015 Holmes Processing

<p>Description: Gathers meta information about a zip file.

<p>Usage: ip-address:port/zipmeta/sampleID
        """
        self.write(description)


class ZipMetaApp(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', Info),
            (r'/zipmeta/([a-zA-Z0-9\-]*)', ZipMetaProcess),
        ]
        settings = dict(
            template_path=path.join(path.dirname(__file__), 'templates'),
            static_path=path.join(path.dirname(__file__), 'static'),
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.engine = None


def main():
    server = tornado.httpserver.HTTPServer(ZipMetaApp())
    server.listen(7715)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
