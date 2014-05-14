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
	doUpload(options.root_dir)

	

def getOptions():
	try:
		parser=OptionParser()
		parser.add_option('-d', '--dir', dest='root_dir', help='The directory containing all the process directories')
		(options, args) = parser.parse_args()
		if not options.root_dir:
			print "We can't do this without a root directory..."
			sys.exit(1)
		tools.ensureDirsExist(options.root_dir)
	except IOError as e:
		print e.strerror
		print "The center cannot hold - exiting..."
		sys.exit(1)

	return options

def doUpload(root_dir):
	for d in os.listdir(root_dir):
		abs_path = os.path.join(root_dir, d)
		# skip any non-directory files
		if not os.path.isdir(abs_path): continue
		os.system('python upload_to_ojs.py {0}'.format(abs_path))


if __name__ == '__main__':
	main()