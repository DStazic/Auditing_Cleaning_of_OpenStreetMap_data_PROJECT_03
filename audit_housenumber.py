# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python audit_housenumber.py zurich_sample.osm -p 1/2
        -> choose between regex variant 1 or 2
    
    Executing script in python command:
        from audit_housenumber import *
        audit("zurich_sample.osm", True/False, 1/2)
        -> results returned as dictionary and directly printed if True
        -> choose between regex variant 1 or 2
'''

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict


def is_housenumber(element):
    '''
    checks if XML element encodes the attribute key that describes a housenumber
    '''
    return element.attrib["k"] == "addr:housenumber"

invalid_housenumber = defaultdict(set)
def validate_housenumber(element, ver):
    '''
    regular expression check to expose non-valid housenumber entries.
    
    ver: specifies, which regular expression to use for auditing (int)
    
         1. first iteration; match one or more digits, optionally followed by a word character
       
         2. match one or more digits at the start of the string, optionally followed by one letter and match none 
            or more of the following combination at the end of the string: none or more non-word character, none or
            more digits, none or one letter if letter is not preceeded by another letter. Restriction for the end 
            of the string is required in order not to match substrings in case of consecutive letters (e.g, do not 
            match "1 s" in "1 string").
            E.g,  matches "1", "1a", "1 a", "1-1", "1-1b", "1a-1b" but not "somestring 1" or "1 somestring"
       
      
    '''
    # first iteration
    if ver == 1:
        housenumber_re = re.compile(r"^\d+\w{1}?")
    # second iteration
    elif ver == 2:
        housenumber_re = re.compile(r"^\d+[aA-zZ]?(\W*\d*(?<![a-z])[a-z]{0,1})*$", re.I)

    match = housenumber_re.search(element.attrib["v"])
    if not match:
        invalid_housenumber[element.attrib["v"]].add(element.attrib["v"])



def audit(file,p, ver):
    '''
    audit housenumber. parse over OSM file and execute validate_housenumber() if XML element is second level tag
    encoding a housenumber
    '''
    
    for _,element in ET.iterparse(file):
        if element.tag == "node" or element.tag == "way" or element.tag == "relation":
            for tag in element.iter("tag"):
                if is_housenumber(tag):
                    validate_housenumber(tag,ver)


    if p==True:
        pprint.pprint(dict(invalid_housenumber))
    
    return invalid_housenumber



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    parser.add_argument('ver', help='specify, which regex expression to use for auditing', type=int)
    args = parser.parse_args()
    audit(args.file,args.p, args.ver)