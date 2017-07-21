# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python audit_postcode.py zurich_sample.osm -p
    
    Executing script in python command:
        from audit_postcode import *
        audit("zurich_sample.osm", True/False)
        -> results returned as dictionary and directly printed if True
'''

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict


invalid_postcodes = defaultdict(set)
def is_postcode(element):
    '''
    checks if XML element encodes the attribute key that describes a postcode
    '''
    return element.attrib["k"] == "addr:postcode"

def validate_postcode(element):
    '''
    filters values for the attribute "addr:postcode" (in second level element tag) that don't start
    with 8 followed by 3 more digits (expected postcodes for the city of Zurich).
    '''
    postcode_re = re.compile(r"^8\d{3}")
    postcode_match = postcode_re.search(element.attrib["v"])
    if not postcode_match:
        invalid_postcodes[element.attrib["v"]].add(element.attrib["v"])

def audit(file,p):
    '''
    audit postcodes. parse over OSM file and execute validate_postcode() if XML element is second level tag
    encoding a postcode
    '''
    for _,element in ET.iterparse(file):
        if element.tag == "node" or element.tag == "way" or element.tag == "relation":
            for tag in element.iter("tag"):
                if is_postcode(tag):
                    validate_postcode(tag)


    if p==True:
        pprint.pprint(dict(invalid_postcodes))
    
    return invalid_postcodes



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    audit(args.file,args.p)