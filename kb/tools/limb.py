import tools as tools
from errors import DataError
import os

def tocExists(toc_dir):
	'''
	Ensure a .toc file exists in toc directory
	Return filename or None
	'''
	try:
		toc = tools.getFirstFileWithExtension(toc_dir, '.toc')
	except IOError:
		return False
	return toc

def altoFileCountMatches(alto_dir, input_files_dir):
	'''
	Ensure number of alto files is the same as the
	number of input files.
	Return boolean
	'''
	numAlto = len(os.listdir(alto_dir))
	numInputFiles = len(os.listdir(input_files_dir))

	return numAlto == numInputFiles

def pageCountMatches(pdf_input_dir,input_files_dir):
	'''
	Compare num pages in pdfinfo with pages in input 
	picture directory. 
	return boolean 
	'''
	pdf = tools.getFirstFileWithExtension(pdf_input_dir, '.pdf')
	pdfInfo = tools.pdfinfo(os.path.join(pdf_input_dir, pdf))
	numPages = int(pdfInfo['Pages'])
	numInputFiles = len(os.listdir(input_files_dir))
	return numPages == numInputFiles

def alreadyMoved(toc_dir,pdf_input_dir,input_files_dir,alto_dir):
	try:
		performValidations(toc_dir,pdf_input_dir,input_files_dir,alto_dir)
	except DataError:
		return False
	return True

def performValidations(toc_dir,pdf_input_dir,input_files_dir,alto_dir):
	'''
	1: validering af pdf (antal sider i pdf == antal input billeder)
	2: validering af toc-fil (pt. er der en fil - validering ved parsing efterfoelgende)
	3: validering af alto-filer (evt. "er der lige saa mange som input billeder" eller "er der filer")
	
	Throw DataError if any validation fails
	'''
	if not tocExists(toc_dir): 
		raise DataError("TOC not found!")
	if not pageCountMatches(pdf_input_dir,input_files_dir):
		raise DataError("PDF page count does not match input picture count!")
	if not altoFileCountMatches(alto_dir, input_files_dir):
		raise DataError("Number of alto files does not match number of input files.")
	