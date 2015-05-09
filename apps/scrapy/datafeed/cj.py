import csv

from ftplib import FTP

CJ_USERNAME = 
CJ_PASSWORD = 
SERVERNAME = "datatransfer.cj.com/outgoing/productcatalog/"
FILENAME = {
    8: "Sur La Table - Sur La Table Product Catalog.txt.gz",
}

def download_product_datafeed(store_id):
    ftp = FTP(SERVERNAME)
    ftp.login(CJ_USERNAME, CJ_PASSWORD)
    ftp.cwd("/opt/secondfunnel/app/") # This might just be "/"
    
    # Save file on disk as same name
    filename = FILENAME[int(store_id)]

    with open(filename, 'wb') as outfile:
        try:
            ftp.retrbinary("RETR {}".format(filename), outfile.write)
        except Exception as e:
            print 'FTP download failed!\n{}: {}'.format(e.__class__.__name__, e)

    return filename

def delete_product_datafeed(filename):
    pass

def load_product_datafeed(filename, collect_fields, lookup_fields=['SKU','NAME']):
    """ Takes in a CSV product datafeed, and generates a product lookup table

    collect_fields: array of fieldnames to collect for each product
    lookup_fields: keys to generate a lookup table for

    returns: dict of lookup fields, each containing a lookup table for that field as keys
    """
    if not collect_fields:
        collect_fields = ["SKU", "NAME", "DESCRIPTION", "PRICE", "SALEPRICE", "BUYURL", "INSTOCK"]

    lookup_table = {}
    for i in lookup_fields:
        lookup_table[i] = {}

    with open(filename, 'rb') as infile:
        csv_file = csv.DictReader(infile, delimiter=',')
        for row in csv_file:
            # Correct for encoding errors
            entry = { f: row[f].decode("utf-8").encode("latin1").decode("utf-8") for f in fields }

            for i in lookup_fields:
                lookup_table[i][entry[i].encode('ascii', errors='ignore')] = entry

            print entry["NAME"].encode('ascii', errors='ignore')

    print u"Generated lookup table's for {} products".format(len(sku_lookup_table))

    return lookup_table
