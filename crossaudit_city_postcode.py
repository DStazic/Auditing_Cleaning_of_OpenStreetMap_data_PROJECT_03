# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict
from audit_postcode import is_postcode
from audit_city import is_city



expected_POSTCODES = ["8001","8002","8003","8004","8005","8006","8008","8032","8037","8038","8041","8044","8045",
                     "8046","8047","8048","8049","8050","8051","8052","8053","8055","8057","8064"]


invalid_crossref = defaultdict(int)
def cross_validate(city_attrib, postcode_attrib):
    '''
    return unexpected combinations of postcodes and city name
    '''
    if city_attrib == u"Zürich" and postcode_attrib not in expected_POSTCODES:
        invalid_crossref[u"wrong postcode {0} for {1}".format(postcode_attrib,city_attrib)] += 1
    
    if city_attrib != u"Zürich" and postcode_attrib in expected_POSTCODES:
        invalid_crossref[u"wrong city -{1}- for postcode {0}".format(postcode_attrib,city_attrib)] += 1
    



def audit(file,p):
    '''
    cross audit city and postcode. parse over OSM file, extract city and postcode values for specified XML element
    and execute validate_housenumber()
    '''
    city = False
    postcode = False
    for _,element in ET.iterparse(file):
        if element.tag == "node" or element.tag == "way" or element.tag == "relation":
            for tag in element.iter("tag"):
                if is_city(tag):
                    city = tag.attrib["v"]
                if is_postcode(tag):
                    postcode = tag.attrib["v"]
            cross_validate(city, postcode)


    if p==True:
        pprint.pprint(dict(invalid_crossref))
    
    return invalid_crossref



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    audit(args.file,args.p)