#!/usr/bin/python

'''
Created on 26/03/2014

@author: jeel
'''


import os, subprocess, csv, codecs
import shutil


def fix_path(p, check_p = False, logger=None):
    '''
    Add "\" or "/" to the end of p. Also check if p is a dir if check_p.
    Input: path w/wo trailing "/" or "\"
    
    Output: path w trailing "/" or "\" and error msg if check_p=True
    '''
    if not p:
        msg = 'No path given.'
        logger.error(msg)
        return p,msg
    if check_p:
        if not os.path.exists(p):
            msg = p+' does not exist or cannot be accessed'
            if logger: logger.error(msg)
            return p,msg
        elif not os.path.isdir(p):
            msg = p+' is does not a valid directory.'
            if logger: logger.error(msg)
            return p,msg
        p = os.path.normpath(p) + os.sep
        return p,None
    else:
        p = os.path.normpath(p) + os.sep
        return p,None


def find_or_create_dir(path):
    '''
    Given a folder path, check to see 
    if folder exists or create it
    Raises exception in case of error
    '''
    if os.path.exists(path):
        if not os.path.isdir(path):
            error = '{0} exists but is not a valid directory.'.format(path)
            raise IOError(error)
    elif not os.path.exists(path):
        os.makedirs(path)

def move_file(file_path,dest_folder,logger=None):
    '''
    Moves a file from file_path to dest_folder.
    Checks paths and logs errors.
    '''
    # E.g. add try-catch
    check_file(file_path)
    check_folder(dest_folder)
    try:
        '''
        shutil.move doc:
        "If the destination is on the current filesystem, then os.rename() is 
        used. Otherwise, src is copied (using shutil.copy2()) to dst and then 
        removed."
        '''
        shutil.move(file_path, dest_folder)
        msg = 'File '+file_path+' moved corretly to '+dest_folder
        if logger: logger.debug(msg)
    except Exception as e:
        #TODO: an error will occur if file already exist in dest. Fix this
        #Error msg: Destination path ... already exists
        error = 'An error occured when copying '+file_path+' to '+dest_folder+\
            '. Error msg: '+str(e)
        if logger: logger.error(error)
        raise Exception(error)
    return True

def getFileExt(name): 
        return name.split('.')[-1]
    
def get_delta_time(s):
    h, remainder = divmod(s, 3600)
    remainder = round(remainder,3)
    m, remainder = divmod(remainder, 60)
    s, ms = divmod(remainder, 1)
    ms = round(ms,3)*1000
    return '%s h, %s min, %s sec and %s ms' % (int(h), int(m), int(s), int(ms))
    # Example
    # s = 1221358.258
    # result = 339 h, 15 min, 58 sec and 258 ms

def check_file(file_path) :
    '''
    Checks a file_path. Returns True if it exist, else raises error.
    '''
    if not file_path:
        raise NameError('Argument "file_path" not set.') 
    elif not os.path.exists( file_path ) :
        raise IOError('File "' + file_path + '" does not exist.')
    else:
        if not os.path.isfile( file_path ) :
            raise IOError('File "' + file_path + '" is not a file_path.')
        else:
            with open( file_path ) : pass
    return True

def check_folder(folder):
    if not folder:
        raise NameError('Argument "folder" not set.')
    elif not os.path.exists( folder ) :
        raise IOError('Folder "' + folder + '" does not exist.')
    else:
        if not os.path.isdir( folder ) :
            raise IOError('Folder "' + folder + '" is not a folder.')
    return True

def create_folder(path):
    error = None
    if not path:
        error = 'Argument "path" not set.'
    elif not os.path.exists(path):
        try:
            os.makedirs(path)
        except IOError as e:
            error = e.strerror
    return error

def checkDirectoriesExist(*args):
    """
    Given a variable number of directories
    return false if any of them do not exist
    """
    for dir in args:
        if not os.path.isdir(dir):
            print "{0} is not a valid directory.".format(dir)
            return False
    return True


def ensureFilesExist(*args):
    '''
    Given a variable number of file paths
    raise an error if any of them do not exist
    '''
    for file in args:
        if not os.path.isfile(file):
            raise IOError(1, "File {0} could not be found".format(file))

def getFirstFileWithExtension(dir, ext):
    '''
    Return the first file we can find in the given directory
    with the given extension.
    Useful when we don't know the file name
    '''
    for file in os.listdir(dir):
        if file.endswith(ext): return file

    return None

def parseToc(toc):
    '''
    Given a full path to a LIMB toc file
    return a lists of dictionaries
    where each dictionary corresponds to 
    a line in the toc
    e.g. [{level: "1", author: "Annemarie Lund", title: "Arbejder fra Vibeke Roennows tegnestue", page: "5"}]
    if there is no pipe character in the TOC title field, author will be blank
    e.g. {'title': 'Front Matter', 'author': '', 'page': '1', 'level': '0'}
    TODO: this method should be improved to handle Unicode properly
    but since we only need page numbers for now, I'm putting it on the long finger
    See https://docs.python.org/2/library/csv.html#csv-examples to get started
    '''
    data = []
    with open(toc, 'r') as toc_csv:
        reader = csv.reader(toc_csv, delimiter=',', quotechar='"')
        iterreader = iter(reader) # skip the first line as this just contains header data
        next(iterreader)
        for row in iterreader:
            try:
                level = row[0]
                if '|' in row[1]:
                    author = row[1].split('|')[0]
                    title = row[1].split('|')[1]
                else: 
                    author = ""
                    title = row[1]
                page = row[2]

                data.append(dict(level=level, author=author,title=title, page=page))    
            # if there's some problem with the input row, skip it
            except IndexError:
                print "ERROR - TOC row not parsed successfully {0}".format(",".join(row))
    
    return data        

def pdfinfo(infile):
    """
    Wraps command line utility pdfinfo to extract the PDF meta information.
    Returns metainfo in a dictionary.
    sudo apt-get install poppler-utils
     
    This function parses the text output that looks like this:
    Title: PUBLIC MEETING AGENDA
    Author: Customer Support
    Creator: Microsoft Word 2010
    Producer: Microsoft Word 2010
    CreationDate: Thu Dec 20 14:44:56 2012
    ModDate: Thu Dec 20 14:44:56 2012
    Tagged: yes
    Pages: 2
    Encrypted: no
    Page size: 612 x 792 pts (letter)
    File size: 104739 bytes
    Optimized: no
    PDF version: 1.5
    """
     
    cmd = '/usr/bin/pdfinfo'
    if not os.path.exists(cmd):
        raise RuntimeError('System command not found: %s' % cmd)
     
    if not os.path.exists(infile):
        raise RuntimeError('Provided input file not found: %s' % infile)

    #if "check_output" not in dir( subprocess ):
     #   implementCheckOutput()
     
    def _extract(row):
        """Extracts the right hand value from a : delimited row"""
        return row.split(':', 1)[1].strip()
     
    output = {}
     
    labels = ['Title', 'Author', 'Creator', 'Producer', 'CreationDate',
    'ModDate', 'Tagged', 'Pages', 'Encrypted', 'Page size',
    'File size', 'Optimized', 'PDF version']
     
    # cmd_output = subprocess.check_output([cmd, infile])
    # the above line is default, but won't work on Python 2.6. The below is a workaround
    cmd_output = subprocess.Popen([cmd, infile], stdout=subprocess.PIPE).communicate()[0]
    
    for line in cmd_output.splitlines():
        for label in labels:
            if label in line:
                output[label] = _extract(line)
 
    return output

def cutPdf(inputPdf, outputPdf, fromPage, toPage):
    '''
    Wrapper around pdftk - create outputPdf from the range
    specified in from, to based on inputPdf
    will return false if exit code is not 0 (i.e. an error code)
    '''
    page_range = "{0}-{1}".format(fromPage, toPage)
    exit_code = subprocess.call(['pdftk', inputPdf, 'cat', page_range, 'output', outputPdf])
    
    return exit_code == 0 