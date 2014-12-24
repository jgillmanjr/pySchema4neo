#!/usr/bin/python

"""
A layer to provide for dataconsistency utilizing a schema

Author: Jason Gillman Jr.
"""

import py2neo
import json

def validateSchema(schema, validator):
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
					if not hasattr(validator, propDef['validator']):
						raise Exception('Node property validator ' + propDef['validator'] + ' is not defined in the validator module')

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
									if not hasattr(validator, propDef['validator']):
										raise Exception('Relation property validator ' + propDef['validator'] + ' is not defined in the validator module')


class Schema():
	"""
	The Schema class
	"""
	def __call__(self, *args, **kwargs):
		"""
		If the things pass validation, they get created or updated.

		Also return a list of the results in the order of the arguments as they were passed in
		"""
		argResults = []
		if args:
			for arg in args:
				argClass = arg.__class__.__name__
				if argClass == 'Node': argResults.append(self.checkNode(arg))
				if argClass == 'Relationship': argResults.append(self.checkRel(arg))
				if argClass not in ['Node', 'Relationship']: argResults.append({'success': False, 'err': 'Umm, not sure what to do with an instance of' + argClass})

		return argResults

	def __init__(self, schemaPath, validatorModule, graphObj):
		"""
		Insantiate a Schema object.

		schemaPath is the path to the JSON file containing your schema

		validatorModule is the python module containing your validators

		graphObj is the py2neo Graph object to use
		"""
		# Load the validator module
		self.validator = __import__(validatorModule)

		# Schema setup and validation
		schemaFile = open(schemaPath)
		self.schema = json.loads(schemaFile.read())
		schemaFile.close()
		validateSchema(self.schema, self.validator) # Make sure things are on the up and up

		self.Graph = graphObj
	
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

		propValidator = {} # This will associate a label property with the validator. This will be used to make sure duplicate property names defined for a label don't conflict with others
		for nodeLabel in nodeLabels:
			if nodeLabel not in self.schema:
				return {'success': False, 'err': nodeLabel + ' is not a valid label'}
			else:
				if 'requiredProperties' in self.schema[nodeLabel] and len(self.schema[nodeLabel]['requiredProperties']) > 0:
					requiredProps = self.schema[nodeLabel]['requiredProperties']
					for reqPropKey, reqPropDef in requiredProps.iteritems():
						if reqPropKey not in nodeProperties.keys():
							return {'success': False, 'err': 'The required node property ' + reqProp + ' is not defined in the node.'}
						else:
							if reqPropKey not in propValidator:
								propValidator[reqPropKey] = reqPropDef['validator']
							else:
								if reqPropDef['validator'] != propValidator[reqPropKey]: return {'success': False, 'err': 'Validator conflict for node property: ' + reqPropKey} # Check for the conflict and return if needed
						
						validateResult = self.validate(reqPropDef['validator'], nodeProperties[reqPropKey]) # Validate the property
						if not validateResult['success']:
							return {'success': False, 'err': reqPropKey + ' failed validation: ' + validateResult['err']}
		
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
			ncResult = self.checkNode(Rel.start_node, True)
			if not ncResult['success']:
				return {'success': False, 'err': 'The starting node failed validation: ' + ncResult['err']}
		if nodeChkLoc != 'End':
			ncResult = self.checkNode(Rel.end_node, True)
			if not ncResult['success']:
				return {'success': False, 'err': 'The ending node failed validation: ' + ncResult['err']}

		# Now make sure the relation itself is legit
		
		## Check the relation type for validity
		startNode		= Rel.start_node
		startLabels		= set(startNode.labels)
		endNode			= Rel.end_node
		endLabels		= set(endNode.labels)
		relProperties	= Rel.properties
		allowedRel = False # This will indicate whether the relation type is considered legit from the perspective of the node's label(s)
		freeForAll = False # Set if there's a 'free for all' label assigned to the starting node
		
		## 'Free for all' check
		if self.anyRelLabels.intersection(startLabels):
			allowedRel = True # Not really needed, but my OCD compels me..
			freeForAll = True

		## If not a free for all, do further checks
		if not freeForAll:
			### Check to make sure the relation type is valid for the label(s) in the starting node and check against target labels as well as conflict check the properties
			labelRelTargets = {} # Will store the valid targets of a relation
			relPropValidator = {} # Will be used for relation property conflict detection
			for startLabel in startLabels:
				if Rel.type in self.schema[startLabel]['validRelations']:
					allowedRel = True
					if len(self.schema[startLabel]['validRelations'][Rel.type]) > 0: # The start label in question has defined target labels for the relation type
						labelRelTargets[startLabel] = set()
						for tgtLbl, tgtDef in self.schema[startLabel]['validRelations'][Rel.type].iteritems():
							labelRelTargets[startLabel].add(tgtLbl)
							if len(tgtDef) > 0: # The target definition specifies properties the relation must have
								for tPropKey, tPropDef in tgtDef.iteritems():
									if tPropKey not in relProperties.keys():
										return {'success': False, 'err': 'The required property ' + tPropKey + ' is not defined in the relation.'}
									else:
										if tPropKey not in relPropValidator:
											relPropValidator[tPropKey] = tPropDef['validator']
										else:
											if tPropDef['validator'] != relPropValidator[tPropKey]: return {'success': False, 'err': 'Validator conflict for relation property ' + tPropKey} # Check for the conflict
									
									validateResult = self.validate(tPropDef['validator'], relProperties[tPropKey]) # Validate the property
									if not validateResult['success']:
										return {'success': False, 'err': tPropKey + ' failed validation: ' + validateResult['err']}

				#### Check to make sure the target node has at least one label that is a valid target for each of the start nodes labels for a given relation type
				if startLabel in labelRelTargets:
					if not labelRelTargets[startLabel] & endLabels:
						return {'success': False, 'err': 'The target node does not possess at least one of the required labels based on the start node\'s labels and the relation type.'}

			if not allowedRel: return {'success': False, 'err': 'The relation type ' + Rel.type + ' is not one allowed by any of the starting node\'s labels.'}

		# Execute relation creation or update
		if Rel.bound:
			Rel.push() # Update
		else:
			self.Graph.create(Rel) # Create
		return {'success': True, 'err': None}

	def validate(self, valName, propValue):
		"""
		Run the input against the validator specified by valName

		valName is the name of the validator

		propValue is the data to be evaluated
		"""

		return getattr(self.validator, valName)(propValue)
