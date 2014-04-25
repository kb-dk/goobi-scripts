from goobi.goobi_step import Step

class EmptyStep( Step ):

	def setup(self):
		self.name = 'A tester'
		self.config_main_section = 'test'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			'process_id' : 'number',
			'process_path' : 'folder'
		}

	def step(self):
		return None

if __name__ == '__main__':
	
	EmptyStep( ).begin()