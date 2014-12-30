#!/usr/bin/python
"""
Generate a pySchema4neo shell schema file from a neo4j database

describeLabel - The label you want to use to indicate what nodes to pull to generate the shell

schemaName - The name of the output file

host and port should be self explanitory
"""

import py2neo
import json

describeLabel = raw_input('Label to use [domainDescribe]: ')
if not describeLabel:
	describeLabel = 'domainDescribe'

schemaName = raw_input('Schema file name (omit extension) [yourSchema]: ')
if not schemaName:
	schemaName = 'yourSchema'

host = raw_input('Host to use [http://localhost]: ')
if not host:
	host = 'http://localhost'

port = raw_input('Port to use [7474]: ')
if not port:
	port = '9494'

dbString	= host + ':' + port + '/db/data/'

myGraph = py2neo.Graph(dbString)

domNodes = myGraph.find(describeLabel)

validLabels = {}

for node in domNodes:
	print node['name']
	if node['name'] not in validLabels:
		validLabels[node['name']] = {'validRelations': {}, 'requiredProperties': {}}
		if 'properties' in node: # Get the required properties for a node label
			print "\tProperties"
			for prop in node['properties']:
				print "\t  =>" + prop
				validLabels[node['name']]['requiredProperties'][prop] = {'validator': '', 'description': ''}
			print ""
	for rel in node.match_outgoing():
		print "\t-[:" + rel.type + "]->" + str(rel.end_node['name'])
		if rel.type not in validLabels[node['name']]['validRelations']:
			validLabels[node['name']]['validRelations'][rel.type] = {}
		validLabels[node['name']]['validRelations'][rel.type][rel.end_node['name']] = {}
		if 'properties' in rel: # Get the required properties for the relation->target
			for prop in rel['properties']:
				print "\t--  " + prop
				validLabels[node['name']]['validRelations'][rel.type][rel.end_node['name']][prop] = {'validator': '', 'description': ''}
	
	print ""	

jsonString = json.dumps(validLabels, sort_keys=True, indent = 4, separators=(',', ': '))

dumpFile = open(schemaName + '.json', 'w')

dumpFile.write(jsonString)

dumpFile.close()


