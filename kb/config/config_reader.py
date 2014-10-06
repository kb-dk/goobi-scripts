#!/usr/bin/env python
# -*- coding: utf-8
import configparser
import codecs


class ConfigSection:
	""" Dummy class to create attributes in """
	pass
	
class ConfigReader:
	'''
		Easy access config values. This reads in the configuration values and creates attributes for each. Spaces in names are replaced with underscores
		
		e.g.:
			config.ini :
				[my section]
				myname = my value

			read.py :
				c = ConfigReader( "config.ini" )
				print(c.my_section.myname # output string "my value")
	'''
	
	def __init__(self, filename, old_config=None,overwrite_sections=False,
				 overwrite_options=False):
		settings = configparser.ConfigParser()
		settings.readfp( codecs.open( filename, encoding="utf-8", mode="rb") )
		if old_config:
			old_config = old_config.config
			for section in old_config.sections():
				if overwrite_sections and settings.has_section(section):
					continue
				settings.add_section(section)
				for name, value in old_config.items( section ):
					if overwrite_options and settings.has_option(section, name):
						continue
					settings.set(section, name, value)
		self.config = settings
		
		for section in settings.sections() :
			section_name = section.replace( " ", "_" )
			new_section = ConfigSection()
			vars(self) [section_name] = new_section
			
			for name, value in settings.items( section ):
				if value.lower() == "true" :
					vars( new_section )[name] =  True
				elif value.lower() == "false" :
					vars( new_section )[name] =  False
				else :
					vars( new_section )[name] =  value
					
	def hasSection( self, section_name ):
		return section_name in self.config.sections()
	
	def hasItem( self, section_name, item_name ):
		return section_name in self.config.sections() and item_name in [n for n,_ in self.config.items(section_name)]
		
	def item( self, section_name, item_name ):
		item = None
		if self.hasItem( section_name, item_name ):
			item = vars( vars(self)[section_name] )[item_name]
		return item
		
if __name__ == '__main__' :

	c = ConfigReader( "../config.ini" )
	
	print('Has section "DUMMY": ' + str( c.hasSection( "DUMMY" ) ))
	
	hasDatabank = c.hasSection( "databank" )
	print('Has section "databank" : ' + str( hasDatabank ))
	if hasDatabank:
	
		print('Has item "databank.dummy": ' + str(c.hasItem( "databank", "dummy" ) ))
		
		hasDatabankHost = c.hasItem( "databank", "host" )
		print('Has item "databank.host" : ' + str( hasDatabankHost ))
		
		if hasDatabankHost:
			print("Databank host = " + c.databank.host)

	
	