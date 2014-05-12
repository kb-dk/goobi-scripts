#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step

from tools import tools
from tools.errors import DataError
import os, sys
class ValidateLimbOutput( Step ):

	def setup(self):
		self.name = 'ValidateLimbOutput'
		self.config_main_section = 'limb_output'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			'process_title' : 'string',
			'auto_report_problem' : 'string',
			'step_id' : 'string'
		}


	def step(self):
		'''
		This class checks the output from a LIMB process
		to see if it matches certain criteria
		Require params process_title from command line
		Other values taken from config.ini
		In the case of errors a message will be returned
		and sent to the previous step.
		'''
		try:
			self.getVariables()
			self.performValidations()
			return None
		except IOError as e:
			return "IOError - directory not found {0}".format(e.strerror)	
		except DataError as e: 
			return "Validation error - {0}.".format(e.strerror)


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

		# throw Error if one of our directories is missing
		tools.ensureDirsExist(self.limb_dir, self.alto_dir, \
			self.toc_dir, self.pdf_dir, self.input_files_dir)


	def performValidations(self):
		'''
		1: validering af pdf (antal sider i pdf == antal input billeder)
		2: validering af toc-fil (pt. er der en fil - validering ved parsing efterfoelgende)
		3: validering af alto-filer (evt. "er der lige saa mange som input billeder" eller "er der filer")

		Throw DataError if any validation fails
		'''
		if not self.tocExists(): 
			raise DataError("TOC not found!")
		if not self.pageCountMatches():
			raise DataError("PDF page count does not match input picture count!")
		if not self.altoFileCountMatches():
			raise DataError("Number of alto files does not match number of input files.")

		self.info_message("All validations performed successfully.")
		

	def tocExists(self):
		'''
		Ensure a .toc file exists in toc directory
		return (string) filename
		TODO: A similar method has been created in the generic 
		tools.limb module - callers to this method should use that instead
		and this method should be removed
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
		'''
		TODO: A similar method has been created in the generic 
		tools.limb module - callers to this method should use that instead
		and this method should be removed.
		'''
		self.info_message("Comparing number of Alto files with input files")
		numAlto = len(os.listdir(self.alto_dir))
		numInputFiles = len(os.listdir(self.input_files_dir))

		return numAlto == numInputFiles

if __name__ == '__main__':
	
	ValidateLimbOutput().begin()