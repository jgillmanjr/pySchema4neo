"""
An example validator module to go with the example schema

In the event of successful validation, a dict of {'success': True, 'err': None} should be returned

In the event of a failed validation, a dict of {'success': False, 'err': 'Enter your informational message here'} should be returned
"""

def integer(input):
	"""
	Make sure the input can at least be converted to an integer
	"""
	try:
		int(input)
	except Exception:
		return {'success': False, 'err': 'Not an integer and could not convert to an integer'}

	return {'success': True, 'err': None}

def string(input):
	"""
	Make sure the input can at least be converted to a string
	"""
	try:
		str(input)
	except Exception:
		return {'success': False, 'err': 'Not a string and could not convert to a string'}
	return {'success': True, 'err': None}

def codeExEnum(input):
	try:
		enumList = ['rookie', 'midlevel', 'veteran']
		if input not in enumList:
			joiner = ', '
			return {'success': False, 'err': input + ' is not in list of values ' + joiner.join(enumList)}
	except Exception:
		return {'success': False, 'err': 'Some error occured'}

	return {'success': True, 'err': None}

def conflict(input):
	return {'success': True, 'err': None}
