#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step

from tools import tools
import os, sys
class ValidateLimbOutput( Step ):

	def setup(self):
		self.name = 'ValidateLimbOutput'
		self.config_main_section = 'limb_output'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			'process_title' : 'string',
			'process_path' : 'folder'
		}


	def step(self):
		'''
		This class checks the output from a LIMB process
		to see if it matches certain criteria
		Require params process_title from command line
		Other values taken from config.ini
		'''
		if self.getVariables():
			if self.performValidations():
				self.info_message("All validations performed successfully.")
				sys.exit(0)
			else: 
				self.error_message("At least one validations failed - exiting...")
		else:
			self.error_message("Failed to set all variables successfully - exiting...")
		
		sys.exit(1)

	

	def getVariables(self):
		'''
		Get all required vars from command line + config
		and confirm their existence.
		'''
		process_title = self.command_line.process_title
		limb = self.getConfigItem('limb_output')
		alto = self.getConfigItem('alto')
		toc = self.getConfigItem('toc')
		pdf = self.getConfigItem('pdf')
		inputs = self.getConfigItem('input_files')

		# join paths to create absolute paths
		self.limb_dir = os.path.join(limb, process_title)
		self.alto_dir = os.path.join(self.limb_dir, alto)
		self.toc_dir = os.path.join(self.limb_dir, toc)
		self.pdf_dir = os.path.join(self.limb_dir, pdf)
		self.input_files_dir = os.path.join(self.limb_dir, inputs)

		# return false if one of our directories is missing
		return tools.checkDirectoriesExist(self.limb_dir, self.alto_dir, \
			self.toc_dir, self.pdf_dir, self.input_files_dir)


	def performValidations(self):
		'''
		1: validering af pdf (antal sider i pdf == antal input billeder)
		2: validering af toc-fil (pt. er der en fil - validering ved parsing efterfoelgende)
		3: validering af alto-filer (evt. "er der lige saa mange som input billeder" eller "er der filer")
		'''
		if not self.tocExists(): 
			self.error_message("TOC not found!")
			return False
		if not self.pageCountMatches():
			self.error_message("pdf page count does not match input picture count!")
			return False
		if not self.altoFileCountMatches():
			self.error_message("Number of alto files does not match number of input files.")
			return False

		return True

	def tocExists(self):
		'''
		Ensure a .toc file exists in toc directory
		return (string) filename
		'''
		self.info_message("Checking for toc in {0}".format(self.toc_dir))
		toc = tools.getFirstFileWithExtension(self.toc_dir, '.toc')
		return toc

	
	def pageCountMatches(self):
		'''
		Compare num pages in pdfinfo with pages in input 
		picture directory. 
		return boolean 
		'''
		self.info_message("Comparing page count with input files")
		pdf = tools.getFirstFileWithExtension(self.pdf_dir, '.pdf')
		pdfInfo = tools.pdfinfo(os.path.join(self.pdf_dir, pdf))
		numPages = int(pdfInfo['Pages'])
		numInputFiles = len(os.listdir(self.input_files_dir))

		return numPages == numInputFiles

	def altoFileCountMatches(self):
		self.info_message("Comparing number of Alto files with input files")
		numAlto = len(os.listdir(self.alto_dir))
		numInputFiles = len(os.listdir(self.input_files_dir))

		return numAlto == numInputFiles

if __name__ == '__main__':
	
	ValidateLimbOutput().begin()