# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python data.py zurich_sample.osm
        -> validation of dictionary structure
        
        python data.py zurich_sample.osm -validation
        -> no validation of dictionary structure
    
    Executing script in python command:
        from data import *
        process_map("zurich_sample.osm", True/False)
        -> writes csv files from XML data; includes validation of dictionary structure if True
    '''

'------------------------------'
'GENERAL MODULES'
'------------------------------'
import pandas as pd
import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import argparse
import cerberus
import db_schema


'------------------------------'
'FUNCTIONS FROM AUDIT SCRIPTS'
'------------------------------'
from crossaudit_city_postcode import expected_POSTCODES
from audit_city import is_city
from audit_street import is_street
from audit_postcode import is_postcode
from audit_housenumber import is_housenumber

'------------------------------'
'CLEANING SCRIPTS'
'------------------------------'
from osm_cleaning import *

'-----------------------------------'
'FUNCTIONS SHAPING XML ELEMENTS'
'-----------------------------------'
# refrence file for correcting/updating tag dictionaries
reference = pd.read_csv("street_names_zipcodes_zurich_update", dtype = str)
reference = reference.set_index(reference["street"].values)

def update_tag_dict(reference,id_tag,tag_city_dict, tag_street_dict, tag_postcode_dict,tag_district_dict, tag_quarter_dict):
    '''
        updates dictionaries storing tag data according to the reference dataset. Updates require valid dictionary
        with street data (tag_street_dict not None).
        '''
    is_Zurich = False
    
    def update_city(id_tag, value):
        tag_city_dict["id"] = id_tag
        tag_city_dict["key"] = "city"
        tag_city_dict["value"] = value
        tag_city_dict["type"] = "addr"
    def update_postcode(id_tag, value):
        tag_postcode_dict["id"] = id_tag
        tag_postcode_dict["key"] = "postcode"
        tag_postcode_dict["value"] = value
        tag_postcode_dict["type"] = "addr"
    def update_district(id_tag, value):
        tag_district_dict["id"] = id_tag
        tag_district_dict["key"] = "district"
        tag_district_dict["value"] = value
        tag_district_dict["type"] = "addr"
    def update_quarter(id_tag, value):
        tag_quarter_dict["id"] = id_tag
        tag_quarter_dict["key"] = "quarter"
        tag_quarter_dict["value"] = value
        tag_quarter_dict["type"] = "addr"
    
    if tag_street_dict:
        # encoding unicode in byte-type string representation required for index search in reference database when
        # street value decoded as unicode
        street = tag_street_dict["value"].encode("utf-8")
        
        # check if street name ending with "gass" is actually "gasse"-type ("gass", either misspelling or swiss
        # dialect). Substitution for "gasse" makes sure that OSM street names with "gass" can be compared with
        # reference dataset (in reference dataset only "gasse" type versus OSM data with "gass" and "gasse")
        gass_re = re.compile(r"gass$")
        match_gass = gass_re.search(street)
        if match_gass:
            street = re.sub(gass_re, "gasse", street)
        
        try:
            # if street part of Zurich, update district and quarter dictionaries with relevant data
            reference.loc[street]
            
            # unique street match will return pandas Series object as street variable
            if isinstance(reference.loc[street], pd.Series):
                
                if tag_city_dict and (tag_city_dict["value"] == u"Zürich"):
                    update_postcode(id_tag, reference.loc[street]["zipcode"])
                    is_Zurich = True
                
                if tag_postcode_dict and (tag_postcode_dict["value"] in expected_POSTCODES):
                    update_city(id_tag, u"Zürich")
                    is_Zurich = True
                
                if is_Zurich:
                    update_district(id_tag, reference.loc[street]["district"])
                    update_quarter(id_tag, reference.loc[street]["quarter"])
                
                # Assumption that element is Zurich if street is part of Zurich and no information about postcode or city
                if not tag_city_dict and not tag_postcode_dict:
                    update_city(id_tag, u"Zürich")
                    update_postcode(id_tag, reference.loc[street]["zipcode"])
                    update_district(id_tag, reference.loc[street]["district"])
                    update_quarter(id_tag, reference.loc[street]["quarter"])
        
            # multiple street matches will return pandas Dataframe object as street variable
            elif isinstance(street, pd.DataFrame) and tag_postcode_dict:
                for idx in range(len(reference.loc[street])):
                    if reference.loc[street].iloc[idx]["zipcode"] == tag_postcode_dict["value"]:
                        update_city(id_tag, u"Zürich")
                        update_district(id_tag, reference.loc[street]["district"])
                        update_quarter(id_tag, reference.loc[street]["quarter"])

        except KeyError:
            # if street not part of Zurich, keep original city value or update city to Zürich municipality if
            # no city dictionary or Zürich as city value
            if not tag_city_dict or (tag_city_dict["value"] == u"Zürich"):
                update_city(id_tag, u"Zürich municipality")




def get_tag_key_type(element, default_tag_type='regular'):
    '''
    returns key and type for each tag. if no ":" in tag "k" value, it is set as the tag key and tag type is set as
    "regular". if ":" in tag "k" value, the string before the ":" is set as tag type and string after the ":" is 
    set as tag key. if there are additional ":" in the "k" value they and they should be ignored and remain part of
    the tag key. E.g:
    
    <tag k="addr:street:name" v="Lincoln"/>
    should be turned into
    {'id': 12345, 'key': 'street:name', 'value': 'Lincoln', 'type': 'addr'}
    '''
    
    
    one_colon = re.compile(r"^[\w|_]+:[\w|_]+$")
    two_colon = re.compile(r"^[\w|_]+:[\w|_]+:[\w|_]+$")
    
    if one_colon.search(element.attrib["k"]):
        tag_type,key = element.attrib["k"].split(":")
    
    elif two_colon.search(element.attrib["k"]):
        tag_type = element.attrib["k"].split(":")[0]
        key = ":".join(element.attrib["k"].split(":")[1:])
    else:
        key = element.attrib["k"]
        tag_type = default_tag_type
    
    return (tag_type, key)



def create_clean_tag_dicts(element, id_tag):
    '''
    tag (second level XML element) data for each first level XML element (node, way, relation) is cleaned, if 
    appropriate, and stored as a dictionary
    
    element: XML tag element returned by ElementTree
    id_tag: id attribute value of the parental XML element (node, way, relation)
    '''
    
    one_colon = re.compile(r"^[\w|_]+:[\w|_]+$")
    two_colon = re.compile(r"^[\w|_]+:[\w|_]+:[\w|_]+$")
    
    bool_city = False
    bool_street = False
    bool_postcode = False
    generic_tag_dict = None
    
    if is_city(element):
        value = city_clean(element)
        bool_city = True
    elif is_street(element):
        value = street_clean(element, mapping_street)
        bool_street = True
    elif is_postcode(element):
        value = postcode_clean(element)
        bool_postcode = True
    elif is_housenumber(element):
        value = housenumber_clean(element)
    else:
        value = element.attrib["v"]

    tag_type, key = get_tag_key_type(element)

    if value:
        generic_tag_dict = {"id": id_tag,
                            "key": key,
                            "value": value,
                            "type": tag_type}

    return generic_tag_dict, bool_city, bool_street, bool_postcode

# match also empty strings (via negative lookahead ^(?![\s\S]))
PROBLEMCHARS = re.compile(r'^(?![\s\S])|[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
SCHEMA = db_schema.schema

def specify_store_tag_dicts(element, problem_chars,id_tag,tags):
    '''
    specifies tag dictionaries returned by create_clean_tag_dicts() function -which is required for updating the
    dictionaries by the update_tag_dict() function- and stores all tag dictionaries (updated) as a list for each 
    cognate parental element.
    
    element: XML tag element returned by ElementTree
    id_tag: id attribute value of the parental XML element (node, way, relation)
    problem_chars: set of characters not allowed to be present in tag attribute values
    '''
    
    tag_city_dict = {}
    tag_street_dict = {}
    tag_postcode_dict = {}
    tag_district_dict = {}
    tag_quarter_dict = {}
    
    for tag in element.iter("tag"):
        if problem_chars.search(tag.attrib["k"].strip()):
            continue
        else:
            generic_tag_dict, bool_city, bool_street, bool_postcode = create_clean_tag_dicts(tag,id_tag)
            # exclude tag if value is None
            if not generic_tag_dict:
                continue
            else:
                if bool_city:
                    tag_city_dict = generic_tag_dict.copy()
                elif bool_street:
                    tag_street_dict = generic_tag_dict.copy()
                elif bool_postcode:
                    tag_postcode_dict = generic_tag_dict.copy()
                elif generic_tag_dict:
                    tags.append(generic_tag_dict)

    # use reference data to update/correct tags
    update_tag_dict(reference, id_tag, tag_city_dict, tag_street_dict, tag_postcode_dict, tag_district_dict, tag_quarter_dict)
    for tag_dict in [tag_city_dict, tag_street_dict,tag_postcode_dict,tag_district_dict,tag_quarter_dict]:
        if tag_dict:
            tags.append(tag_dict)


# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS =["id","user","uid","version","lat","lon","timestamp","changeset"]
NODE_TAGS_FIELDS = ["id", "key", "value", "type"]

WAY_FIELDS =["id","user","uid","version","timestamp","changeset"]
WAY_TAGS_FIELDS = ["id", "key", "value", "type"]
WAY_NODES_FIELDS = ["id", "node_id", "position"]

RELATIONS_FIELDS =["id","user","uid","version","timestamp","changeset"]
RELATIONS_TAGS_FIELDS = ["id", "key", "value", "type"]
RELATIONS_MEMBERS_FIELDS = ["id", "member_id", "member_role", "member_type", "position"]

def shape_element(element, problem_chars=PROBLEMCHARS, NODE_primary_attributes = NODE_FIELDS,
                  WAY_primary_attributes = WAY_FIELDS, RELATIONS_primary_attributes = RELATIONS_FIELDS,
                  default_tag_type='regular'):
    """Clean and shape node, way or relation XML element to Python dict"""
    
    node_attribs = {}
    way_attribs = {}
    relation_attribs = {}
    way_nodes = []
    relation_nodes = []
    relation_ways = []
    tags = []  # Handle secondary tags the same way for node, way and relation elements
    
    
    if element.tag == 'node':
        for key in NODE_primary_attributes:
            node_attribs[key] = element.attrib[key]
        
        specify_store_tag_dicts(element, problem_chars,node_attribs["id"],tags)
        
        return {'node': node_attribs, 'node_tags': tags}

    if element.tag == 'way':
        for key in WAY_primary_attributes:
            way_attribs[key] = element.attrib[key]
        
        specify_store_tag_dicts(element, problem_chars,way_attribs["id"],tags)
        
        for idx,node in enumerate(element.iter("nd")):
            way_nodes.append({"id":way_attribs["id"], "node_id":node.attrib["ref"], "position":idx})

        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
    
    if element.tag == 'relation':
        for key in RELATIONS_primary_attributes:
            relation_attribs[key] = element.attrib[key]
        
        specify_store_tag_dicts(element, problem_chars,relation_attribs["id"],tags)
        
        for idx,member in enumerate(element.iter("member")):
            member_role = member.attrib["role"]
            # if member attribs match problematic characters assign "unknown"; not required for the ways ref
            # attribs, as those have been checked for irregularities before (see auditing id's)
            if problem_chars.search(member.attrib["role"]):
                member_role ="unknown"
            if member.attrib["type"] == "node":
                relation_nodes.append({"id":relation_attribs["id"], "member_id":member.attrib["ref"],
                                      "member_role":member_role,"member_type":member.attrib["type"], "position":idx})
            elif member.attrib["type"] == "way":
                relation_ways.append({"id":relation_attribs["id"], "member_id":member.attrib["ref"],
                         "member_role":member_role,"member_type":member.attrib["type"], "position":idx})
                         
    return {'relation': relation_attribs, 'relation_nodes': relation_nodes,'relation_ways': relation_ways, 'relation_tags': tags}


'-------------------------------------------------'
'FUNCTION FOR WRITING CSV FILES FOR THE DATABASE'
'-------------------------------------------------'


NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"
RELATIONS_PATH = "relations.csv"
RELATIONS_NODES_PATH = "relations_nodes.csv"
RELATIONS_WAYS_PATH = "relations_ways.csv"
RELATIONS_TAGS_PATH = "relations_tags.csv"



def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""
    
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""
    
    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
        k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems() })
    
    # iterate over list and call writerow method
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def process_map(file, validate):
    """
    Iteratively process each XML element and write to csv(s)
    
    validate: True or False; defines if dictionary structures should be validated (according to defined schema)
    """
    
    
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
        codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
        codecs.open(WAYS_PATH, 'w') as ways_file, \
        codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
        codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file, \
        codecs.open(RELATIONS_PATH, 'w') as relations_file, \
        codecs.open(RELATIONS_NODES_PATH, 'w') as relations_nodes_file, \
        codecs.open(RELATIONS_WAYS_PATH, 'w') as relations_ways_file, \
        codecs.open(RELATIONS_TAGS_PATH, 'w') as relations_tags_file:
                
        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)
        relations_writer = UnicodeDictWriter(relations_file, RELATIONS_FIELDS)
        relations_nodes_writer = UnicodeDictWriter(relations_nodes_file, RELATIONS_MEMBERS_FIELDS)
        relations_ways_writer = UnicodeDictWriter(relations_ways_file, RELATIONS_MEMBERS_FIELDS)
        relations_tags_writer = UnicodeDictWriter(relations_tags_file, RELATIONS_TAGS_FIELDS)
        
        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        relations_writer.writeheader()
        relations_nodes_writer.writeheader()
        relations_ways_writer.writeheader()
        relations_tags_writer.writeheader()
        
        validator = cerberus.Validator()
        
        for element in get_element(file, tags=('node', 'way', 'relation')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
                elif element.tag == 'relation':
                    relations_writer.writerow(el['relation'])
                    relations_nodes_writer.writerows(el['relation_nodes'])
                    relations_ways_writer.writerows(el['relation_ways'])
                    relations_tags_writer.writerows(el['relation_tags'])



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'creating SQL db from OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-validate', action="store_false", default=True)
    args = parser.parse_args()
    
    process_map(args.file, args.validate)

