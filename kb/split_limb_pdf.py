from goobi.goobi_step import Step

from tools import tools
import os, sys
class SplitPdf( Step ):

	def setup(self):
		self.name = 'Pdf splitter'
		self.config_main_section = 'limb_output'
		self.essential_config_sections = set( [] )
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

		# join paths to create absolute paths
		self.limb_dir = os.path.join(limb, process_title)
		self.toc_dir = os.path.join(self.limb_dir, toc)
		self.pdf_dir = os.path.join(self.limb_dir, pdf)

		# return false if one of our directories is missing
		return tools.checkDirectoriesExist(self.limb_dir, self.toc_dir, self.pdf_dir)
	
	def getToc(self):
		toc = tools.getFirstFileWithExtension(self.toc_dir, '.toc')
		self.toc_data = tools.parseToc(os.path.join(self.toc_dir, toc))

	def dividePdf(self):
		''' 
		Cut up the volume into articles pdfs based on the data in the LIMB toc
		'''
		pdf_name = tools.getFirstFileWithExtension(self.pdf_dir, '.pdf')
		pdf_path = os.path.join(self.pdf_dir, pdf_name)
		pdfinfo = tools.pdfinfo(pdf_path)
		counter = 0
		for article in self.toc_data:
			if article['title'] == 'Body': continue # skip the body entry as it doesn't contain anything
			counter += 1
			start_page = int(article['page'])
			index = self.toc_data.index(article)

			# we need to figure out how to get the end page for the article
			if index != len(self.toc_data) - 1: # if this is not the last article
				next_item = self.toc_data[index + 1]
				if self.overlapping_articles: 
					# last page is the start of the next items page
					end_page = int(next_item['page']) 
				else:
					# when we're not doing overlapping pages
					# last page is the page before the next item's start page 
					# unless that page is less than current page
					if int(next_item['page'])-1 >= start_page:
						end_page = int(next_item['page']) -1
					else:
						end_page = start_page
			# if this is the last article - we need to take until the pdf's end page
			# as given by pdfinfo
			else:
				end_page = int(pdfinfo['Pages'])
			# output name is <volumename>_<article number>.pdf
			output_name = "{0}_{1}.pdf".format(pdf_path.replace('.pdf', ''), counter)
			self.info_message("creating file {0}".format(output_name))

			# if our call to pdftk fails, get out quickly
			if not tools.cutPdf(pdf_path,  output_name, start_page, end_page):
				self.error_message("PDF division failed! Exiting...")
				sys.exit(1)

		return None

	def profit(self):
		''' ChaChing! '''

if __name__ == '__main__':
	
	SplitPdf( ).begin()
