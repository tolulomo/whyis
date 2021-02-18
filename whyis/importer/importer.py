import requests
import rdflib
from whyis import nanopub
import datetime
import pytz
import dateutil.parser
from dateutil.tz import tzlocal
from werkzeug.datastructures import FileStorage
from werkzeug.http import http_date
from setlr import FileLikeFromIter
import re
import os
from requests_testadapter import Resp
import magic
import mimetypes
import traceback
import sys

from whyis.namespace import np, prov, dc, sio


class Importer:
    min_modified = 0

    import_once = False

    def last_modified(self, entity_name, db, nanopubs):
        old_nps = [nanopubs.get(x) for x, in db.query('''select ?np where {
    ?np np:hasAssertion ?assertion.
    ?assertion a np:Assertion; prov:wasQuotedFrom ?mapped_uri.
}''', initNs=dict(np=np, prov=prov), initBindings=dict(mapped_uri=rdflib.URIRef(entity_name)))]
        modified = None
        for old_np in old_nps:
            m = old_np.modified
            if m is not None:
                m = m
                # m = pytz.utc.localize(m)
            if m is None:
                continue
            if modified is None or m > modified:
                print(m, modified, old_np.modified)
                modified = m
        return modified

    def load(self, entity_name, db, nanopubs):
        entity_name = rdflib.URIRef(entity_name)
        print("Fetching", entity_name)
        old_nps = [nanopubs.get(x) for x, in db.query('''select ?np where {
    ?np np:hasAssertion ?assertion.
    ?assertion a np:Assertion; prov:wasQuotedFrom ?mapped_uri.
}''', initNs=dict(np=np, prov=prov), initBindings=dict(mapped_uri=rdflib.URIRef(entity_name)))]
        updated = self.modified(entity_name)
        if updated is None:
            updated = datetime.datetime.now(pytz.utc)
        #try:
        g = self.fetch(entity_name)
        #except Exception as e:
        #    print("Error loading %s: %s" % (entity_name, e))
        #    traceback.print_exc(file=sys.stdout)
        #    return
        for new_np in nanopubs.prepare(g):
            print("Adding new nanopub:", new_np.identifier)
            self.explain(new_np, entity_name)
            new_np.add((new_np.identifier, sio.isAbout, entity_name))
            if updated is not None:
                new_np.pubinfo.add(
                    (new_np.assertion.identifier, dc.modified, rdflib.Literal(updated, datatype=rdflib.XSD.dateTime)))
            for old_np in old_nps:
                new_np.pubinfo.add((old_np.assertion.identifier, prov.invalidatedAtTime,
                                    rdflib.Literal(updated, datatype=rdflib.XSD.dateTime)))
            nanopubs.publish(new_np)

        for old_np in old_nps:
            print("retiring", old_np.identifier)
            nanopubs.retire(old_np.identifier)

    def explain(self, new_np, entity_name):
        activity = rdflib.BNode()
        new_np.provenance.add((activity, rdflib.RDF.type, self.app.NS.whyis.KnowledgeImport))
        new_np.provenance.add((new_np.assertion.identifier, prov.wasGeneratedBy, activity))
        new_np.provenance.add((activity, prov.used, rdflib.URIRef(entity_name)))
        new_np.provenance.add((new_np.assertion.identifier, prov.wasQuotedFrom, rdflib.URIRef(entity_name)))
        new_np.provenance.add((new_np.assertion.identifier, prov.wasDerivedFrom, rdflib.URIRef(entity_name)))
