import sys, os
import ConfigParser
from optparse import OptionParser

import tools.tools as tools

def main():
	'''
	Given a directory path from the command line,
	iterate over it, running the two necessary scripts for each
	sub directory.
	'''
	options = getOptions()
	doUpload(options)


def doUpload(options):
	for d in os.listdir(options.root_dir):
		abs_path = os.path.join(options.root_dir, d)
		# skip any non-directory files
		if not os.path.isdir(abs_path): continue

		args = buildArgs(abs_path, options)
		uploadFiles(args)
		runImportScript(args)
		

def buildArgs(abs_path, options):
	'''
	Generate the arguments that will be used by both scripts
	'''
	abs_config = os.path.abspath(options.settings)
	process_title = getProcessTitle(abs_path, abs_config)
	args = "process_id=1 process_path={0} process_title={1} config_path={2}"\
		.format(abs_path, process_title, abs_config)
	# if there are options for debug settings, add it
	if options.debug: args += " debug=true"
	return args

def uploadFiles(args):
	'''
	call upload step with args
	'''
	print('python upload_to_ojs.py {0}'.format(args))
	os.system('python upload_to_ojs.py {0}'.format(args))
	

def runImportScript(args):
	'''
	Call import script with args
	'''
	print('python run_ojs_import.py {0}'.format(args))
	os.system('python run_ojs_import.py {0}'.format(args))

def getProcessTitle(path, config_file):
	'''
	We assume that the process title for the given directory
	is the same as the name of the toc file minus .toc
	'''
	config = ConfigParser.RawConfigParser()
	config.read(config_file)
	toc_dir = os.path.join(path, config.get('process_folder_structure', 'metadata_toc_path'))
	toc_name = tools.getFirstFileWithExtension(toc_dir, 'toc')
	return toc_name[:-4]

def getOptions():
	try:
		parser=OptionParser()
		parser.add_option('-d', '--dir', dest='root_dir', help='The directory containing all the process directories.')
		parser.add_option('-c', '--settings', dest='settings', 
			help='The settings file to be read by the scripts. If not specified, the system default will be assumed.')
		parser.add_option('-v', '--debug', dest='debug', help='Should the scripts run in debug mode?')
		(options, args) = parser.parse_args()
		ensureValidOptions(options, parser)
		tools.ensureDirsExist(options.root_dir)
	except IOError as e:
		print(e.strerror)
		print(parser.print_help())
		sys.exit(1)

	return options

def ensureValidOptions(options, parser):
	if not options.root_dir:
		exitWithError("We can't do this without a root directory...", parser)
	if not options.settings:
		exitWithError("We cant do this without a settings file...", parser)
		
	# if we have a debug argument - convert it to boolean
	if options.debug:
		options.debug = (options.debug.lower() == 'true')

def exitWithError(msg, parser):
	print(msg)
	print(parser.print_help())
	sys.exit(1)

if __name__ == '__main__':
	main()