import csv
import gzip
import os

from ftplib import FTP

from apps.utils.classes import LookupTable


class RakutenDatafeed(object):
    """ Rakuten datafeed download & parser.  Intended to be wrapped for each customer """
    RAK_USERNAME = "fraserharris"
    RAK_PASSWORD = "J5Pz9bJ4"
    RAK_SERVERNAME = "aftp.linksynergy.com"

    def __init__(self, store, datafeed):
        """ Expected format of datafeed = {
            'filename': '', # filename for downloading datafeed
            'pathname': '', # path to datafeed on Rakuten FTP
            'field_mapping': [] # key names for interpreting the raw feed data
        }
        """
        self.store = store
        self.datafeed = datafeed
        self.filename = datafeed['filename']
        self.keys = datafeed['field_mapping']

    def _download(self):
        """ Downloads the Rakuten product datafeed for "store" if it is setup

        raises: LookupError if store is not set up for Rakuten product datafeed

        return: filename where download is saved"""
        ftp = FTP(self.RAK_SERVERNAME)
        ftp.login(self.RAK_USERNAME, self.RAK_PASSWORD)
        ftp.cwd("/")

        with open(self.filename, 'wb') as outfile:
            print "Downloading {} product datafeed: {}".format(self.store.name, self.filename)
            try:
                ftp.retrbinary("RETR {}{}".format(self.datafeed['pathname'], self.filename), outfile.write)
            except Exception as e:
                raise IOError('FTP download failed!\n{}: {}'.format(e.__class__.__name__, e))

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
                csv_file = csv.reader(infile, delimiter='|')
                for row in csv_file:
                    # map data to values using keys
                    rowdata = dict(zip(self.keys, row))
                    # Correct for encoding errors
                    try:
                        entry = { f: rowdata[f] for f in collect_fields }
                    except KeyError:
                        print "ERROR: following row could not be parsed: {}".format(rowdata)
                        continue
                    lookup_table.add(entry= entry,
                                     mappings= [ (f, entry[f].encode('ascii', errors='ignore')) for f in lookup_fields])
                    product_counter += 1

            print u"Generated lookup tables for {} products".format(product_counter)
        finally:
            self._delete()

        return lookup_table

    def _delete(self):
        print "Deleting product datafeed: {}".format(self.filename)
        try:
            os.remove(self.filename)
        except OSError:
            pass
