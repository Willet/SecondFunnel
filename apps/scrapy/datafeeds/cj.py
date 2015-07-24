import csv
import gzip
import os

from ftplib import FTP

from apps.scrapy.models import LookupTable


class Datafeed(object):
    """ CJ datafeed download & parser.  Intended to be wrapped for each customer """
    CJ_USERNAME = "4503838"
    CJ_PASSWORD = "7JTu@6Xb"
    CJ_SERVERNAME = "datatransfer.cj.com"

    name = None # Store slug

    def __init__(self, store, datafeed):
        """ Expected format of datafeed = {
            'filename': '', # filename for downloading datafeed
            'pathname': '' # path to datafeed on CJ FTP
        }
        """
        self.store = store
        self.datafeed = datafeed
        self.filename = datafeed.filename

    def load(self, collect_fields=["SKU", "NAME", "DESCRIPTION", "PRICE", "SALEPRICE",\
                                   "BUYURL", "INSTOCK"], lookup_fields=['SKU','NAME']):
        """ Download the product datafeed and generate the product lookup table

        collect_fields: array of fieldnames to collect for each product
        lookup_fields: keys to generate a lookup table for

        returns: dict of lookup fields and the hash table
        each lookup field a lookup table for that field as keys, returning the hash key for the entry in the hash table
        """
        try:
            self._download() # Download the datafeed

            product_counter = 0

            lookup_table = LookupTable(lookup_fields)

            with gzip.open(self.filename, 'rb') as infile:
                csv_file = csv.DictReader(infile, delimiter=',')
                for row in csv_file:
                    # Correct for encoding errors
                    entry = { f: row[f].decode("utf-8").encode("latin1").decode("utf-8") for f in collect_fields }
                    lookup_table.add(entry= entry,
                                     mappings= [ (f, entry[f].encode('ascii', errors='ignore')) for f in lookup_fields])
                    product_counter += 1

            print u"Generated lookup table's for {} products".format(product_counter)
        finally:
            self._delete()

        return lookup_table

    def _download(self):
        """ Downloads the CJ product datafeed for "store" if it is setup

        raises: LookupError if store is not set up for CJ product datafeed

        return: filename where download is saved"""
        ftp = FTP(CJ_SERVERNAME)
        ftp.login(CJ_USERNAME, CJ_PASSWORD)
        ftp.cwd("/")

        with open(self.filename, 'wb') as outfile:
            print "Downloading {} product datafeed: {}".format(store.name, self.filename)
            try:
                ftp.retrbinary("RETR {}{}".format(self.datafeed['PATHNAME'], self.filename), outfile.write)
            except Exception as e:
                raise IOError('FTP download failed!\n{}: {}'.format(e.__class__.__name__, e))

    def _delete(self):
        print "Deleting product datafeed: {}".format(self.filename)
        os.remove(self.filename)
