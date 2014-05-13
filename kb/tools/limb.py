import tools as tools
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
	