#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step

from tools import tools
import os, sys
class SplitPdf( Step ):

	def setup(self):
		self.name = 'Pdf splitter'
		self.config_main_section = 'limb_output'
		self.essential_config_sections = set( ['limb_output', 'process_folder_structure'] )
		self.essential_commandlines = {
			'process_title' : 'string',
			'process_path' : 'folder',
			'overlapping_articles' : 'string'
		}

	def step(self):
		'''
		Splits a pdf file according to a toc file
		1. set necessary variables
		2. get data from toc file
		3. cut up pdf file
		4. profit!
		'''
		self.getVariables()
		self.getToc()
		self.dividePdf()
		self.profit()

		return None

	def getVariables(self):
		'''
		Get all required vars from command line + config
		and confirm their existence.
		'''
		# parse boolean from command line
		if self.command_line.overlapping_articles.lower() == 'true':
			self.overlapping_articles = True
		elif self.command_line.overlapping_articles.lower() == 'false':
			self.overlapping_articles = False
		else:
			self.error_message("Invalid value {0} given for overlapping_articles argument - exiting..." \
				.format(self.command_line.overlapping_articles))
			sys.exit(1)
		
		process_title = self.command_line.process_title
		limb = self.getConfigItem('limb_output')
		toc = self.getConfigItem('toc')
		pdf = self.getConfigItem('pdf')
		pdf_output = self.getConfigItem('doc_pdf_path', None, 'process_folder_structure')
		self.pdf_output_dir = os.path.join(self.command_line.process_path, pdf_output)

		# join paths to create absolute paths
		self.limb_dir = os.path.join(limb, process_title)
		self.toc_dir = os.path.join(self.limb_dir, toc)
		self.pdf_dir = os.path.join(self.limb_dir, pdf)
		self.pdf_name = tools.getFirstFileWithExtension(self.pdf_dir, '.pdf')
		self.pdf_path = os.path.join(self.pdf_dir, self.pdf_name)
		self.pdfinfo = tools.pdfinfo(self.pdf_path)

		# return false if one of our directories is missing
		return tools.checkDirectoriesExist(self.limb_dir, self.toc_dir, self.pdf_dir, self.pdf_output_dir)
	
	def getToc(self):
		toc = tools.getFirstFileWithExtension(self.toc_dir, '.toc')
		self.toc_data = tools.parseToc(os.path.join(self.toc_dir, toc))
		self.toc_data = tools.enrichToc(self.toc_data, self.pdfinfo, self.overlapping_articles)

	def dividePdf(self):
		''' 
		Cut up the volume into articles pdfs based on the data in the LIMB toc
		TODO: shouldn't use sys.exit, should throw an Exception
		'''

		for index, article in enumerate(self.toc_data):
			output_name = tools.getArticleName(self.pdf_name, index)
			output_path = os.path.join(self.pdf_output_dir, output_name)
			self.info_message("creating file {0}".format(output_path))

			# if our call to pdftk fails, get out quickly
			if not tools.cutPdf(self.pdf_path,  output_path, article['start_page'], article['end_page']):
				self.error_message("PDF division failed! Exiting...")
				sys.exit(1)

		return None

	def profit(self):
		''' ChaChing! '''

if __name__ == '__main__':
	
	SplitPdf( ).begin()
