# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python audit_id_version.py zurich_sample.osm -p
    
    Executing script in python command:
        from audit_id_version import *
        audit("zurich_sample.osm", True/False)
        -> results returned as dictionary and directly printed if True
'''

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict



invalid_id_version = defaultdict(set)
def validate_id_version(element):
    '''
    checks if id (id or uid attributes in first level element node; ref attribute in second level elements nd and
    member) or version attribute (in first level element node, way, relation) can be converted to integer type.
    Non-valid entries are stored in the set invalid_id_version.
    '''
    
    try:
        int(element.attrib["id"])
    except ValueError:
        invalid_id_version["invalid element id"].add(element.attrib["id"])
    try:
        int(element.attrib["uid"])
    except ValueError:
        invalid_id_version["invalid user id"].add(element.attrib["uid"])
    try:
        int(element.attrib["version"])
    except ValueError:
        invalid_id_version["invalid version"].add(element.attrib["version"])

    if element.tag == "way":
        for nd in element.iter("nd"):
            try:
                int(nd.attrib["ref"])
            except ValueError:
                invalid_id_version["invalid node reference in way"].add(nd.attrib["ref"])

    if element.tag == "relation":
        for member in element.iter("member"):
            try:
                int(member.attrib["ref"])
            except ValueError:
                invalid_id_version["invalid node reference in relation"].add(member.attrib["ref"])


def audit(file,p):
    '''
    audit id, uid and version. parse over OSM file and execute validate_id() function with specified XML elements
    '''
    for _,element in ET.iterparse(file):
        if element.tag == "node" or element.tag == "way" or element.tag == "relation":
            validate_id(element)


    if p==True:
        pprint.pprint(dict(invalid_id_version))
    
    return invalid_id_version



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    audit(args.file,args.p)