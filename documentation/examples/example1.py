#!/usr/bin/python

import sys
sys.path.append('../../') # So we can load pySchema4neo from this location (assuming you haven't stuck it somewhere else in path already)

from pySchema4neo import Schema
import py2neo

myGraph = py2neo.Graph()
mySchema = Schema('exampleSchema.json', 'exampleValidator', myGraph)

node1 = py2neo.Node('Person', name = 'Bob', age = 26)
node2 = py2neo.Node('Person', name = 'Jim', age = 29)
node3 = py2neo.Node('ProgLanguage', name = 'Python')

print mySchema(node1) # [{'err': None, 'success': True}]
print mySchema(node1, node2) # [{'err': None, 'success': True}, {'err': None, 'success': True}]

rel1 = py2neo.Relationship(node1, 'knows', node2, length = 3)
print mySchema(rel1) # [{'err': None, 'success': True}]

rel2 = py2neo.Relationship(node1, 'knows', node3)
print mySchema(rel2) # [{'err': u'The target node has no label(s) that fall into the allowed list of [Person]', 'success': False}]
rel2.type = 'codesIn'
print mySchema(rel2) # [{'err': u'Required property experience is not specified in the relation.', 'success': False}]
rel2['experience'] = 'Low'
print mySchema(rel2) # [{'err': u'The required property experience did not pass validation: Low is not in list of values rookie, midlevel, veteran', 'success': False}]
rel2['experience'] = 'rookie'
print mySchema(rel2) # [{'err': None, 'success': True}]


myGraph.delete(node1, node2, node3, rel1, rel2) # Cleanup
