import sys, os
import tools.tools as tools
from optparse import OptionParser

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

		config = options.config if options.config else None
		args = buildArgs(abs_path, config)
		uploadFiles(args)
		runImportScript(args)
		

def buildArgs(abs_path, config):
	'''
	Generate the arguments that will be used by both scripts
	'''
	args = "process_id=1 process_path={0} process_title=lan-01-2008".format(abs_path)
	# if we haven't supplied a config, goobi step will try to guess one
	if config: args += " config_path={0}".format(os.path.abspath(config))
	return args

def uploadFiles(args):
	'''
	build the args for the script
	'''
	print 'python upload_to_ojs.py {0}'.format(args)
	os.system('python upload_to_ojs.py {0}'.format(args))

def runImportScript(path):
	print "running import script"

def getOptions():
	try:
		parser=OptionParser()
		parser.add_option('-d', '--dir', dest='root_dir', help='The directory containing all the process directories.')
		parser.add_option('-c', '--config', dest='config', 
			help='The config file to be read by the scripts. If not specified, the system default will be assumed.')
		(options, args) = parser.parse_args()
		ensureValidOptions(options, parser)
		tools.ensureDirsExist(options.root_dir)
	except IOError as e:
		print e.strerror
		print parser.print_help()
		sys.exit(1)

	return options

def ensureValidOptions(options, parser):
	if not options.root_dir:
		print "We can't do this without a root directory..."
		print parser.print_help()
		sys.exit(1)


if __name__ == '__main__':
	main()