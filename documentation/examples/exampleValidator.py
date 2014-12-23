"""
An example validator module to go with the example schema
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
	return {'success': True, 'err': None}

def codeExEnum(input):
	return {'success': True, 'err': None}

def conflict(input):
	return {'success': True, 'err': None}
