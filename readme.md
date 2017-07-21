
The aim of this project is to audit and clean openstreetmap (OSM) data that is in XML format and describes the city of Zürich (Switzerland). Eventually, cleaned up data will be organized as a SQL database, which will be used to answer questions about the city of Zürich.

The following source was used to extract the data:
http://www.openstreetmap.org/relation/1682248

OSM files used for analysis:
- zurich.osm (compressed file zurich.osm.bz2)
- zurich_sample.osm

Scripts and files used for data auditing:
- audit_city.py
- audit_coordinates.py
- audit_housenumber.py
- audit_id_version.py
- audit_postcodes.py
- audit_reference.py
- audit_street.py
- audit_timestamp.py
- crossaudit_city_postcode.py
- street_names_zipcodes_zurich.csv
- street_names_zipcodes_zurich_update.csv

Files and Scripts used for data cleaning:
- osm_cleaning.py
- street_names_zipcodes_zurich.csv
- street_names_zipcodes_zurich_update.csv

Files and scripts used for data processing  (writing of cvs files required for setting up the SQL database):
- db_schema.py
- data.py

SQL Database containing cleaned data
- zurichOSM.db (compressed file zurichOSM.db.bz2)

cvs files used to create the database are included in csv_files.tar. The database contains following tables:

1. nodes, ways, relations
-> each table contains information on nodes, ways and relations attributes
2. nodes_tags, ways_tags, relations_tags
-> each table contains information on attributes from nodes', ways' and relations' tag elements
3. ways_nodes
-> contains information on attributes from ways' nd elements (refers to node id's)
4. relations_nodes, relations_ways
-> contains information on attributes from relations' member elements (refers to node or way id's)


Scripts can either be executed in python console (e.g jupyter notebook) or via command line. For more details please refer to each script file.
