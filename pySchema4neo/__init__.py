#!/usr/bin/python

"""
A layer to provide for dataconsistency utilizing a schema

Author: Jason Gillman Jr.
"""

import py2neo
import json

def validateSchema(schema):
	"""
	Validate the schema

	schema is the JSON decoded version
	"""

	if type(schema) is not dict or len(schema) == 0:
		raise Exception('Empty Schema or is not a dict')

	for nodeLabel, nodeDef in schema.iteritems():
		location = 'Node Index ' + str(nodeLabel)
		if not isinstance(nodeLabel, basestring):
			raise Exception('Invalid node label in node definition at ' + location)
		if type(nodeDef) is not dict:
			raise Exception(location + ' is not a dict')
		if 'description' in nodeDef and not isinstance(nodeDef['description'], basestring):
			raise Exception('description is not a string at ' + location)

		if 'requiredProperties' in nodeDef:
			if type(nodeDef['requiredProperties']) is not dict:
				raise Exception('requiredProperties for ' + location + 'is not a dict')
			if len(nodeDef['requiredProperties']) > 0: # Dive into requiredProperties
				for propLabel, propDef in nodeDef['requiredProperties'].iteritems():
					location = 'Node Index ' + str(nodeLabel) + ' Property Index: ' + str(propLabel)
					if not isinstance(propLabel, basestring):
						raise Exception('Invalid property label in node definition at ' + location)
					if type(propDef) is not dict:
						raise Exception(location + ' is not a dict')
					if 'validator' not in propDef or not isinstance(propDef['validator'], basestring):
						raise Exception('No validator or invalid validator value for ' + location)
					if 'description' in propDef and not isinstance(propDef['description'], basestring):
						raise Exception('description is not a string at ' + location)

		if 'validRelations' in nodeDef:
			if type(nodeDef['validRelations']) is not dict:
				raise Exception('validRelations for node definition at index ' + location + 'is not a dict')
			if len(nodeDef['validRelations']) > 0: # Dive into validRelations
				for relType, relDef in nodeDef['validRelations'].iteritems():
					location = 'Node Index ' + str(nodeLabel) + ' Relation Index: ' + str(relType)
					if not isinstance(relType, basestring):
						raise Exception('Invalid relation type value in relation definition at ' + location)
					if type(relDef) is not dict:
						raise Exception(location + ' is not a dict')
					if len(relDef) > 0: # Dive into validTargets
						for tgtLabel, tgtDef in relDef.iteritems():
							location = 'Node Index ' + str(nodeLabel) + ' Relation Index: ' + str(relType) + ' Target Index: ' + str(tgtLabel)
							if not isinstance(tgtLabel, basestring):
								raise Exception('Invalid target label in relation definition at ' + location)
							if type(tgtDef) is not dict:
								raise Exception(location + ' is not a dict')
							if len (tgtDef) > 0: # Dive into required properties for the target
								for propLabel, propDef in tgtDef.iteritems():
									location = 'Node Index ' + str(nodeLabel) + ' Relation Index: ' + str(relType) + ' Target Index: ' + str(tgtLabel) + ' Property Index: ' + str(propLabel)
									if not isinstance(propLabel, basestring):
										raise Exception('Invalid property label at ' + location)
									if type(propDef) is not dict:
										raise Exception(location + ' is not a dict')
									if 'validator' not in propDef or not isinstance(propDef['validator'], basestring):
										raise Exception('No validator or invalid validator value for ' + location)
									if 'description' in propDef and not isinstance(propDef['description'], basestring):
										raise Exception('description is not a string at ' + location)


class Graph(py2neo.Graph):
	"""
	An overloaded py2neo.Graph class which contains code to load the schema and validator objects.

	Multiple schema objects can be instantiated.
	"""
	def __new__(cls, schemaPath, validatorPath, uri=None):
		return super(py2neo.Graph, cls).__new__(cls, uri)

	def __init__(self, schemaPath, validatorPath, uri=None):
		"""
		Insantiate a Graph object.

		schemaPath is the path to the JSON file containing your schema

		validatorPath is the path to the script that contains your validators
		"""

		# Schema setup #
		schemaFile = open(schemaPath)
		rawSchema = json.loads(schemaFile.read())
		validateSchema(rawSchema) # Make sure things are on the up and up
		schemaFile.close()

		#validatorFile = open(validatorPath)

class Node(py2neo.Node):
	def __init__(self, *args, **kwargs):
		py2neo.Node.__init__(self, *args, **kwargs)

class Relationship(py2neo.Relationship):
	def __init__(self, *args, **kwargs):
		py2neo.Relationship.__init__(self, *args, **kwargs)
