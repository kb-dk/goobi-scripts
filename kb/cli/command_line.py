#!/usr/bin/env python
# -*- coding: utf-8


import sys


class CommandLine() :
	'''
		Pass parameters and create an object with those parameters. Names can not contain spaces.
		
		e.g. of parameters are "one=something two=something else"
		then CommandLine().one = "something" and CommandLine().two = "something else"
		
		Dots (.) in names will be replaced with underscores (_) 
		
	'''
	
	_error = False
	_errorText = ''
	
	def __init__( self ):
		args = sys.argv[1:] # skip filename
		# Gather args together (avoid spaces splititing values)
		args_list = {}
		last_key = ''
		for i in range(len(args)):
			if "=" not in args[i]:
				if last_key != '':
					args_list[last_key] += " " + args[i]
				else:
					self._error = True
					self._errorText = "First parameter does not contain an equals. Can not proceed."
			else:
				key, value = args[i].split( "=" )
				# Be able to pass parameters wrapped within quotes
				if value.startswith('"'):
					args_list[key.strip()] = value.strip('"')
				else:
					args_list[key.strip()] = value.strip()
				last_key = key.strip()
		self._parameters = args_list
		# Create variables for this on ConfigReader
		for item in args_list:
			item_name = item.replace( ".", "_" )
			vars(self)[item_name] = args_list[item]
			
	def has( self, name ):
		return name in self._parameters
		
	def get( self, name ):
		if self.has( name ) :
			return self._parameters[name]
		else:
			error = 'Argument {0} not given through command line'
			error = error.format(name)
			raise KeyError(error)
		return None
		
	def set( self, name, value ):
		if self.has( name ) :
			self._parameters[name] = str(value)
		
	def error( self ) :
		return self._error;

		