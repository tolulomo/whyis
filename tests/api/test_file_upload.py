from base64 import b64encode

from rdflib import *

from io import BytesIO

from whyis.test.api_test_case import ApiTestCase


class UploadTest(ApiTestCase):
    
    def test_plain_text_upload(self):
        self.login(*self.create_user("user@example.com","password"))
        
        nanopub = '''{ "@id": "http://example.com/testdata","http://vocab.rpi.edu/whyis/hasContent":"data:text/plain;charset=UTF-8,Hello, World!"}'''
        print("POST /pub")
        response = self.client.post("/pub", data=nanopub, content_type="application/ld+json",follow_redirects=True)
        print (response.data, response.status)
            
        self.assertEquals(response.status,'201 CREATED')
        content = self.client.get("/about",query_string={"uri":"http://example.com/testdata"},follow_redirects=True)
        self.assertEquals(content.mimetype, "text/plain")
        self.assertEquals(str(content.data,'utf8'), "Hello, World!")    

    def test_PDF_upload(self):
        self.login(*self.create_user("user@example.com","password"))
        pdf_filename = "tests/test_pdf.pdf"
        pdf_content = u'\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nThis is a test PDF, this is the header. \n\nHello World! This is the body. \nHow are you doing? \n \n  \n\n\n\nThis is a test PDF, this is the header. \n\nThis is page 2. \n\n\n'
        uri = 'http://example.com/testdata_pdf_form_upload'

        pdf_file = open(pdf_filename, "r")
        data = {
            'file': (pdf_file, 'test_pdf.pdf'),
            'upload_type': 'http://purl.org/net/provenance/ns#File'
        }
        response = self.client.post("/about",query_string={"uri":uri}, data=data)
        self.assertEquals(response.status,'302 FOUND')
        content = self.client.get("/about",query_string={"uri":uri},follow_redirects=True)
        self.assertEquals(content.mimetype, "application/pdf")
        self.assertEquals(type(content.data), type("string type"))
        self.assertEquals(tika_parser.from_buffer(content.data)["content"], pdf_content)

        metadata = self.client.get("/about",query_string={"uri":uri, 'view':'describe'},headers={"Accept":"application/ld+json"},follow_redirects=True)
        g = Graph()
        g.parse(data=metadata.data, format="json-ld")
        self.assertTrue(g.resource(URIRef(uri))[RDF.type : URIRef('http://purl.org/net/provenance/ns#File')])

    def test_base64_upload(self):
        self.login(*self.create_user("user@example.com","password"))
        text = "Hello, World!"
        b64text = str(b64encode(bytes(text,'utf8')),'utf8')
        nanopub = '''{ "@id": "http://example.com/testdatab64","http://vocab.rpi.edu/whyis/hasContent":"data:text/plain;charset=UTF-8;base64,%s"}''' % b64text
        response = self.client.post("/pub", data=bytes(nanopub,'utf8'), content_type="application/ld+json",follow_redirects=True)
        
        self.assertEquals(response.status,'201 CREATED')
        content = self.client.get("/about",query_string={"uri":"http://example.com/testdatab64"},follow_redirects=True)
        self.assertEquals(content.mimetype, "text/plain")
        self.assertEquals(str(content.data, 'utf8'), text)

    def test_form_upload(self):
        self.login(*self.create_user("user@example.com","password"))
        text = "Hello, World!"
        uri = 'http://example.com/testdata_form_upload'
        data = {
            'file': (BytesIO(text.encode('utf8')), 'hello_world.txt'),
            'upload_type': 'http://purl.org/net/provenance/ns#File'
        }
        response = self.client.post("/about",query_string={"uri":uri}, data=data, content_type="multipart/form-data")
        self.assertEquals(response.status,'302 FOUND')
        content = self.client.get("/about",query_string={"uri":uri},follow_redirects=True)
        self.assertEquals(content.mimetype, "text/plain")
        self.assertEquals(str(content.data, 'utf8'), text)

        metadata = self.client.get("/about",query_string={"uri":uri, 'view':'describe'},headers={"Accept":"application/ld+json"},follow_redirects=True)
        g = Graph()
        g.parse(data=metadata.data, format="json-ld")
        self.assertTrue(g.resource(URIRef(uri))[RDF.type : URIRef('http://purl.org/net/provenance/ns#File')])
