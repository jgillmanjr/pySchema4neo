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


class Schema():
	"""
	The Schema class
	"""
	def __call__(self, *args, **kwargs):
		"""
		If the things pass validation, they get created or updated.

		Also return a list of the results in the order of the arguments as they were passed in
		"""
		if args:
			argResults = []
			for arg in args:
				argClass = arg.__class__.__name__
				if argClass == 'Node': argResults.append(self.checkNode(arg))
				if argClass == 'Relationship': argResults.append(self.checkRel(arg))
				if argClass not in ['Node', 'Relationship']: print 'Umm, not sure what to do with an instance of', argClass

		return argResults

	def __init__(self, schemaPath, validatorPath, graphObj):
		"""
		Insantiate a Schema object.

		schemaPath is the path to the JSON file containing your schema

		validatorPath is the path to the script that contains your validators

		graphObj is the py2neo Graph object to use
		"""

		# Schema setup and validation
		schemaFile = open(schemaPath)
		self.schema = json.loads(schemaFile.read())
		validateSchema(self.schema) # Make sure things are on the up and up
		schemaFile.close()

		self.Graph = graphObj

		#validatorFile = open(validatorPath)
	
	def checkNode(self, Node):
		"""
		Checks the validity of the node.

		If it passes, the node is created or updated.

		As for the return value, a dict will be returned in the format of:
			{
				'success': True || False,
				'errMsg': 'If false above, the error message indicating why the fail' || None
			}
		"""
		breaker = False # Things will check for this. If it pops true, node fails and won't create (or update)

		nodeLabels = Node.labels
		nodeProperties = Node.properties
		for nodeLabel in nodeLabels:
			if nodeLabel not in self.schema:
				err = 'Oh lawdy:' + nodeLabel + 'is not a valid label!'
				breaker = True
				break
			else:
				if ('requiredProperties' in self.schema[nodeLabel]) and (len(self.schema[nodeLabel]['requiredProperties']) > 0): # Check for existance of required properties for a label. If so, do needful
					requiredProps = self.schema[nodeLabel]['requiredProperties'].keys()
					for reqProp in requiredProps:
						if reqProp not in nodeProperties.keys():
							err = 'The required property ' + reqProp + ' is not defined in the node.'
							breaker = True
							break
						else:
							pass	# This is where the validator for the required property would be called to make sure the property value was legit. But for now... just go
									# Should also figure out how I want to handle different labels with same required property but different validators...
					if breaker: break
			########### I SHOULD PUT SOMETHING HERE TO CHECK AND MAKE SURE UPDATES STILL JIVE WITH RELATIONS ALREADY SET ###############

		if not breaker: # Check if we should create/update or not
			if Node.bound:
				Node.push() # Update
			else:
				self.Graph.create(Node) # Create
			return {'success': True, 'err': None}
		else:
			return {'success': False, 'err': err}

	def checkRel(self, Rel):
		pass
