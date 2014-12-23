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
		schemaFile.close()
		validateSchema(self.schema) # Make sure things are on the up and up

		## Find any labels that don't require any specific properties, as well as labels that handle any outbound relation
		self.anyPropLabels = set()
		self.anyRelLabels = set()
		for label, definition in self.schema.iteritems():
			if 'requiredProperties' not in definition or len(definition['requiredProperties']) == 0: self.anyPropLabels.add(label)
			if 'validRelations' not in definition or len(definition['validRelations']) == 0: self.anyRelLabels.add(label)


		self.Graph = graphObj

		#validatorFile = open(validatorPath)
	
	def checkNode(self, Node, fromRelChk = False):
		"""
		Checks the validity of the node.

		This method is focused on checking the properties of the node.
		If fromRelChk isn't passed in as True, which will happen if this method gets fired by checkRel(), the node is instantiated on neo4j, and there are in or outbound relations, the relations will be checked as well.
		If it passes, the node is created or updated.

		As for the return value, a dict will be returned in the format of:
			{
				'success': True || False,
				'err': 'If false above, the error message indicating why the fail' || None
			}
		"""
		nodeLabels = Node.labels
		nodeProperties = Node.properties

		if not self.anyPropLabels.intersection(nodeLabels): # No point in checking properties if the node has a 'free for all' label assignment
			for nodeLabel in nodeLabels:
				if nodeLabel not in self.schema:
					return {'success': False, 'err': nodeLabel + ' is not a valid label'}
				else:
					requiredProps = self.schema[nodeLabel]['requiredProperties'].keys()
					for reqProp in requiredProps:
						if reqProp not in nodeProperties.keys():
							return {'success': False, 'err': 'The required property ' + reqProp + ' is not defined in the node.'}
						else:
							pass	# This is where the validator for the required property would be called to make sure the property value was legit. But for now... just go
									# Should also figure out how I want to handle different labels with same required property but different validators... actually, handle this at schema validation - don't allow it
		
		# Check for instantiated relations
		inRels = []
		outRels = []
		if Node.bound: # It will complain if not bound
			relGen = Node.match_incoming() ## Inbound relations
			for rel in relGen:
				inRels.append(rel)
			relGen = Node.match_outgoing() ## Outbound relations
			for rel in relGen:
				outRels.append(rel)

		# Check said relations if the node check wasn't kicked off by a relation check
		if not fromRelChk:
			for rel in inRels:
				if not self.checkRel(rel, 'End')['success']:
					return {'success': False, 'err': 'Inbound relation check failed'}
			for rel in outRels:
				if not self.checkRel(rel, 'Start')['success']:
					return {'success': False, 'err': 'Outbound relation check failed'}

		# Execute node creation or update
		if Node.bound:
			Node.push() # Update
		else:
			self.Graph.create(Node) # Create
		return {'success': True, 'err': None}

	def checkRel(self, Rel, nodeChkLoc = None):
		"""
		Checks the validity of the relation.

		This method focuses on checking the relation in general, which includes the nodes.
		If nodeChkLoc is set (either 'Start' or 'End'), it will skip the check on that particular node since that's where the relation check came from.
		If it passes, the relation is created or updated.

		As for the return value, a dict will be returned in the format of:
			{
				'success': True || False,
				'err': 'If false above, the error message indicating why the fail' || None
			}
		"""
		# Apparently py2neo can have Reltionship objects with more than two nodes? Check to make sure it's only two...
		if Rel.order != 2:
			return {'success': False, 'err': 'There are more than two nodes in the Relationship object.'}

		# Make sure the nodes themselves are legit (without doing relation checks - because that would be recursive and bad, yo)
		# However, don't check a node if the nodeCheck() method is what's calling this
		if nodeChkLoc != 'Start':
			if not self.checkNode(Rel.start_node, True)['success']:
				return {'success': False, 'err': 'The starting node failed validation.'}
		if nodeChkLoc != 'End'
			if not self.checkNode(Rel.end_node, True)['success']:
				return {'success': False, 'err': 'The ending node failed validation.'}

		# Now make sure the relation itself is legit
		
		## Check the relation type for validity
		startNode		= Rel.start_node
		startLabels		= startNode.labels
		endNode			= Rel.end_node
		endLabels		= endNode.labels
		relProperties	= Rel.properties
		allowedRel = False # This will indicate whether the relation type is considered legit from the perspective of the node's label(s)
		freeForAll = False # Set if there's a 'free for all' label assigned to the starting node
		
		## 'Free for all' check
		if self.anyRelLabels.intersection(startLabels):
			allowedRel = True # Not really needed, but my OCD compels me..
			freeForAll = True
#		startNode		= Rel.start_node
#		startLabels		= startNode.labels
#		endNode			= Rel.end_node
#		endLabels		= endNode.labels
#		relProperties	= Rel.properties
#		labelRelCovered = False # This will indicate whether the relation type is considered legit from the perspective of the node's label(s)
#		
#		if self.anyPropLabels.intersection(startLabels): labelRelCovered = True # Might as well just take care of this now if appropriate...
#		for startLabel in startLabels:
#			if Rel.type in self.schema[startLabel]['validRelations']:
#				labelRelCovered = True

