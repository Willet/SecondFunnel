import csv
import gzip
import os

from ftplib import FTP

CJ_USERNAME = "4503838"
CJ_PASSWORD = "7JTu@6Xb"
CJ_SERVERNAME = "datatransfer.cj.com"
STORE = {
    'Sur la Table': {
        "PATHNAME": "outgoing/productcatalog/170707/",
        "FILENAME": "Sur_La_Table-Sur_La_Table_Product_Catalog.txt.gz",
    },
}

def download_product_datafeed(store):
    """Downloads the CJ product datafeed for "store" if it is setup

    store: <Store> instance

    raises: LookupError if store is not set up for CJ product datafeed

    return: filename where download is saved"""
    ftp = FTP(CJ_SERVERNAME)
    ftp.login(CJ_USERNAME, CJ_PASSWORD)
    ftp.cwd("/")

    # Save file on disk as same name
    try:
        data = STORE.get(store.name)
    except KeyError:
        raise LookupError("Store ID has no known CJ datafeed")
    filename = data['FILENAME']

    with open(filename, 'wb') as outfile:
        print "Downloading {} product datafeed: {}".format(store.name, filename)
        try:
            ftp.retrbinary("RETR {}{}".format(data['PATHNAME'], filename), outfile.write)
        except Exception as e:
            raise IOError('FTP download failed!\n{}: {}'.format(e.__class__.__name__, e))

    return filename

def delete_product_datafeed(filename):
    print "Deleting product datafeed: {}".format(filename)
    os.remove(filename)

def load_product_datafeed(filename, collect_fields, lookup_fields=['SKU','NAME']):
    """ Takes in a CSV product datafeed, and generates a product lookup table

    collect_fields: array of fieldnames to collect for each product
    lookup_fields: keys to generate a lookup table for

    returns: dict of lookup fields, each containing a lookup table for that field as keys
    """
    product_counter = 0

    if not collect_fields:
        collect_fields = ["SKU", "NAME", "DESCRIPTION", "PRICE", "SALEPRICE", "BUYURL", "INSTOCK"]

    lookup_table = {}
    for i in lookup_fields:
        lookup_table[i] = {}

    with gzip.open(filename, 'rb') as infile:
        csv_file = csv.DictReader(infile, delimiter=',')
        for row in csv_file:
            # Correct for encoding errors
            entry = { f: row[f].decode("utf-8").encode("latin1").decode("utf-8") for f in collect_fields }

            for i in lookup_fields:
                lookup_table[i][entry[i].encode('ascii', errors='ignore')] = entry
            product_counter += 1

    print u"Generated lookup table's for {} products".format(product_counter)

    return lookup_table
