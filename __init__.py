#!/usr/bin/python

"""
A layer to provide for dataconsistency utilizing a schema

Author: Jason Gillman Jr.
"""

from py2neo import Graph, Node, Relationship
import json

def validateSchema(schema):
	"""
	Validate the schema

	schema is the JSON decoded version
	"""

	if type(schema) is not list or len(schema) == 0:
		raise Exception('Empty Schema or is not a list')

	for nodeIdx, nodeDef in enumerate(schema):
		location = 'Node Index ' + str(nodeIdx)
		if type(nodeDef) is not dict:
			raise Exception(location + ' is not a dict')
		if 'label' not in nodeDef or not isinstance(nodeDef['label'], basestring):
			raise Exception('No label or invalid label value in node definition at ' + location)
		if 'description' in nodeDef and not isinstance(nodeDef['description'], basestring):
			raise Exception('description is not a string at ' + location)

		if 'requiredProperties' in nodeDef:
			if type(nodeDef['requiredProperties']) is not list:
				raise Exception('requiredProperties for ' + location + 'is not a list')
			if len(nodeDef['requiredProperties']) > 0: # Dive into requiredProperties
				for propIdx, propDef in enumerate(nodeDef['requiredProperties']):
					location = 'Node Index ' + str(nodeIdx) + ' Property Index: ' + str(propIdx)
					if type(propDef) is not dict:
						raise Exception(location + ' is not a dict')
					if 'name' not in propDef or not isinstance(propDef['name'], basestring):
						raise Exception('No name or invalid name value for ' + location)
					if 'validator' not in propDef or not isinstance(propDef['validator'], basestring):
						raise Exception('No validator or invalid validator value for ' + location)
					if 'description' in propDef and not isinstance(propDef['description'], basestring):
						raise Exception('description is not a string at ' + location)

		if 'validRelations' in nodeDef:
			if type(nodeDef['validRelations']) is not list:
				raise Exception('validRelations for node definition at index ' + location + 'is not a list')
			if len(nodeDef['validRelations']) > 0: # Dive into validRelations
				for relIdx, relDef in enumerate(nodeDef['validRelations']):
					location = 'Node Index ' + str(nodeIdx) + ' Relation Index: ' + str(relIdx)
					if type(relDef) is not dict:
						raise Exception(location + ' is not a dict')
					if 'type' not in relDef or not isinstance(relDef['type'], basestring):
						raise Exception('No type or invalid type value for ' + location)
					if 'validTargets' in relDef:
						if type(relDef['validTargets']) is not list or len(relDef['validTargets']) == 0:
							raise Exception('validTargets is not a list or is empty for ' + location)
						else: # Dive into validTargets
							for tgtIdx, tgtDef in enumerate(relDef['validTargets']):
								location = 'Node Index ' + str(nodeIdx) + ' Relation Index: ' + str(relIdx) + ' Target Index: ' + str(tgtIdx)
								if type(tgtDef) is not dict:
									raise Exception(location + ' is not a dict')
								if 'label' not in tgtDef or not isinstance(tgtDef['label'], basestring):
									raise Exception('No label or invalid label value for ' + location)
								if 'requiredProperties' in tgtDef:
									if type(tgtDef['requiredProperties']) is not list:
										raise Exception('requiredProperties for ' + location + 'is not a list')
									if len(tgtDef['requiredProperties']) > 0: # Dive into requiredProperties
										for propIdx, propDef in enumerate(tgtDef['requiredProperties']):
											location = 'Node Index ' + str(nodeIdx) + ' Relation Index: ' + str(relIdx) + ' Target Index: ' + str(tgtIdx) + ' Property Index: ' + str(propIdx)
											if type(propDef) is not dict:
												raise Exception(location + ' is not a dict')
											if 'name' not in propDef or not isinstance(propDef['name'], basestring):
												raise Exception('No name or invalid name value for ' + location)
											if 'validator' not in propDef or not isinstance(propDef['validator'], basestring):
												raise Exception('No validator or invalid validator value for ' + location)
											if 'description' in propDef and not isinstance(propDef['description'], basestring):
												raise Exception('description is not a string at ' + location)


class schema:
	"""
	A schema object is what will be used to enforce requirements for creating and updating nodes and relations in Neo4j.

	Multiple schema objects can be instantiated.
	"""

	def __init__(self, schemaPath, validatorPath, uri = None):
		"""
		Insantiate a schema object.

		schemaPath is the path to the JSON file containing your schema

		validatorPath is the path to the script that contains your validators

		uri will be fed into py2neo.Graph() to indicate the URI for the graph database
		"""

		if uri is None:
			self.graph = Graph()
		else:
			self.graph = Graph(uri)

		schemaFile = open(schemaPath)
		self.schema = json.loads(schemaFile.read())
		validateSchema(self.schema)
		schemaFile.close()

		#validatorFile = open(validatorPath)

		
