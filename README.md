pySchema4neo
============

A proof of concept designed for use with Nigel Small's [py2neo](https://github.com/nigelsmall/py2neo) library to allow for the use of schema constraints and property validation.

# Installing pySchema4neo
Either download and include in your path, or `pip install pySchema4neo`

# Using pySchema4neo
## The Schema File
The schema file is a JSON file that does what you think it does. In it you will define (node types mean a label(s) applied to a node):

1. The valid node types
1. An optional description for a given node type
1. Zero or more required properties for a given node type
	1. Any defined properties must have a validator
	1. Any defined properties may have an optional description
1. Zero or more valid outbound relations for a given node type
	1. A specified valid outbound relation can have zero or more "targets" (the target node has to have at least one of these labels)
		1. A target can have zero or more required properties
		1. Any defined properties must have a validator
		1. Any defined properties may have an optional description
	1. If no "target types" are specified, any node is treated as a valid target for the given relation type

See the `schemaModel.txt` file in the `documentation` directory to get a look at the format.

### Important Notes About Schema Definitions
While this proof of concept was designed with only a single label being assigned to a node, an attempt has been made to handle multiple label assignements *somewhat* intelligently.

1. When multiple labels are assigned to a node, the property requirements for **ALL** of the assigned labels must be met. If one of the labels doesn't define required properties, you'll still need to have required properties for any other labels set.
1. Any outbound relation type is allowed as long as it exists within the spec for any of the assigned labels. If a label doesn't restrict outbound relation types, you're still limited to a union of the allowed types specified by the other labels.
1. If there is a validator conflict for a node or relation property, the node or relation create/update will fail (and you'll be notified what went wrong).

### Using the Schema File
When you construct the pySchema4neo.Schema object, pass in the path to the file.

See the `examples` directory for `exampleSchema.json`

## The Validator Module
This validator module is really just a python module.

### Notes About the Validator
In it, you define functions to serve as the validator - not surprisingly, you name said functions with the validator name you specify in the schema. All a validator function does is ensure that a property's input passes an arbitrary set of rules that you define.

If the property passes validation, it should return a dict of this format: `{'success': True, 'err': None}`. If it doesn't, `{'success': False, 'err': 'Enter your informational message here'}` would be what you'll want to return.

Note that just because your validator says things are good to go, Neo4j may still bark at you about the value being passed in not being able to be cast to one if its own datatypes (see http://neo4j.com/docs/stable/graphdb-neo4j-properties.html), so it may not be a bad idea to run a check like that as well if you're concerned about catching that sort of thing early.

### Using the Validator
When you construct the pySchema4neo.Schema object, just pass in a string that indicates the name of the validator module (and of course make sure it's in your path)

See the `examples` directory for `exampleValidator.py`

## Will You Finally Tell Me How to Use This Thing??!?
Yeah yeah... the other stuff was important so you can actually use it. But now that you've made it this far....

The first thing you'll need to do (outside of importing the pySchema4neo and py2neo packages), is create a `py2neo.Graph` object just as if you weren't using this pacakge.

After that, instantiate a `pySchema4neo.Schema` object. Here's an example:
`mySchema = pySchema4neo(schemaPath = '/the/path/to/your/schema/file.json', validatorModule = 'yourValidatorModuleName', graphObj = py2neo.Graph)

At this point, you still create `py2neo.Node` and `py2neo.Relationship` just like normal. However, when you want to use the pySchema4neo package, you pass instances of the previous classes into the `pySchema4neo.Schema` object.

### Usage Examples
There are a few ways you can go about doing this

Setup:
```
myGraph = py2neo.Graph()
mySchema = pySchema4neo.Schema('schema.json', 'myValidator', myGraph)

node1	= py2neo.Node('Person', name = 'Bob', age = 26)
node2	= py2neo.Node('Person', name = 'Jim', age = 29)
node3	= py2neo.Node('Person', name = 'Lonely Joe', age = 69)
rel		= py2neo.Relationship(node1, 'knows', node2, length = 3)
```

Check individual nodes:
```
mySchema(node1)
mySchema(node2)
```
or
```
mySchema(node1, node2)
```

The above will validate individual nodes and either create or update them in the database if they pass muster.

You can also pass in relationship objects:
```
mySchema(rel)
```
Passing in a relation will also check the start and end nodes of the relation as if you passed them in individually.

You can also pass in an arbitrary list of node and relationship objects:
```
mySchema(node3, rel)
```

See the examples in the `documentation/examples/` directory.

### Checking Success (or Failure) of the Operation
Calling the schema object will return a list of statuses like `{'success': True, 'err': None}` or `{'success': False, 'err': 'Enter your informational message here'}` based on each object you pass in (and will return `None` if nothing is passed in) that you can use to verify the success of your operations.


# What Now?
**Go forth and do awesome things (and submit issues as you see them)!**

Also, please send me your feedback about the process of 'schemaizing' neo4j
