from distutils.core import setup

version = '0.5'

setup(
	name = 'pySchema4neo',
	packages = ['pySchema4neo'],
	version = version,
	description = "A proof of concept 'schema' layer for Neo4j utilizing py2neo",
	author = 'Jason Gillman Jr.',
	author_email = 'jason@rrfaae.com',
	url = 'https://github.com/jgillmanjr/pySchema4neo',
	download_url = 'https://github.com/jgillmanjr/pySchema4neo/archive/v' + version + '.tar.gz',
	keywords = ['Neo4j'],
	classifiers = [],
)
