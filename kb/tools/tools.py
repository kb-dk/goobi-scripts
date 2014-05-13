#!/usr/bin/python

'''
Created on 26/03/2014

@author: jeel
'''


import os
import subprocess
import csv
import time
import shutil

# Import from tools - same package
import errors


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


def ensureDirsExist(*args):
    '''
    Given a variable number of directory paths
    raise an error if any of them do not exist
    TODO: phase out use of checkDirectoriesExist
    in favour of this method
    '''
    for dir in args:
        if not os.path.isdir(dir):
            raise IOError(1, "{0} is not a valid directory.".format(dir))


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
    # if file not found    
    raise IOError(1, "No file with ext {0} found in dir {1}".format(ext, dir))

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
        # skip the first line as this just contains header data
        iterreader = iter(reader) 
        next(iterreader)
        for row in iterreader:
            for i, val in enumerate(row):
                row[i] = val.decode('utf-8')
            try:
                level = row[0]
                # Skip the Body entry - it doesn't contain anything
                if row[1] == 'Body': continue 
                if '|' in row[1]:
                    author = row[1].split('|')[0].strip()
                    title = row[1].split('|')[1].strip()
                else: 
                    author = ""
                    title = row[1]
                start_page = row[2]

                data.append(dict(level=level, author=author,title=title, start_page=start_page))    
            # if there's some problem with the input row, skip it
            except IndexError:
                print "ERROR - TOC row not parsed successfully {0}".format(",".join(row))

    return data

def enrichToc(toc_data, pdfinfo, overlapping_articles=False):
    '''
    Use data from toc and pdfinfo to add end_page
    info for Toc articles
    returns dict with new end_page field
    '''
    for index, article in enumerate(toc_data):
        # we need to figure out how to get the end page for the article
        start_page = int(article['start_page'])
        if index != len(toc_data) - 1: # if this is not the last article
            next_item = toc_data[index + 1]
            if overlapping_articles: 
                # last page is the start of the next items page
                end_page = int(next_item['start_page']) 
            else:
                # when we're not doing overlapping pages
                # last page is the page before the next item's start page 
                # unless that page is less than current page
                if int(next_item['start_page'])-1 >= start_page:
                    end_page = int(next_item['start_page']) -1
                else:
                    end_page = start_page
        # if this is the last article - we need to take until the pdf's end page
        # as given by pdfinfo
        else:
            end_page = int(pdfinfo['Pages'])
        toc_data[index]['end_page'] = end_page
    return toc_data

def getArticleName(pdf_name, index):
    '''
    Generate article name for OJS articles
    in format <pdf_name>_<index>
    '''
    return "{0}_{1}.pdf".format(pdf_name.replace('.pdf', ''), index)

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


def copy_files(source,dest,transit=None,delete_original=False,wait_interval=60,
               max_retries=5,logger=None,debug=False):
    """
    Copies all file (non recursive) from 'source' directory to 'dest'.
    if 'trasit' directory is given then the files are first copied to this directory, which is then moved to 'dest' dir
    if 'delete_originat' is True, then the original files (in source) are deleted.
    source: string, path to source folder
    dest: string, path to destination folder
    transit: string path to transit folder or None
    delete_original: bool, delete files from source after succesful transfer
    wait_interval: int, wait time between failed copy
    max_retries: int, how many times to retry copy
    logger: object, goobi-logger 
    """
    #TODO: check input paths (not '' or None) and source and transit exist.
    dest_dir = dest
    if transit:
        dest_dir = transit
    src_files = [[l,False] for l in os.listdir(source)]
    attempts = 0;        
    files_not_copied = True
    while files_not_copied and (attempts<max_retries):
        attempts += 1
        if logger and debug: 
            msg = 'Copying files from {0} to {1}'
            msg = msg.format(source,dest_dir)
            logger.debug(msg)
        try: 
            #create destination dir, if it does not exists
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            i = 0
            for src_file in src_files:
                i += 1
                if logger and debug and False: 
                    files_left = len([e for e in src_files if not e[1]])
                    msg = 'Initiating copy of files. {0} files left'
                    msg = msg.format(files_left)
                    logger.debug(msg)
                file_copied = src_file[1] 
                if (not file_copied):
                    full_file_name = os.path.join(source, src_file[0])
                    if (os.path.isfile(full_file_name)):
                        if logger and debug and False: 
                            msg = "Copying file {0}".format(src_file[0])
                            logger.debug(msg)
                        shutil.copy2(full_file_name, dest_dir)
                        src_file[1] = True
                    else:
                        #Remove elem so it doesn't count as a not yet copied file.
                        src_files.remove(src_file)
                        if logger and debug: 
                            msg = ("{0} is not a file ... skipping it")
                            msg.format(full_file_name)
                            logger.debug(msg)
                if (i%50)==0 and logger and debug: 
                    files_left = len([e for e in src_files if not e[1]])
                    msg = 'Initiating copy of files. {0} files left'
                    msg = msg.format(files_left)
                    logger.debug(msg)
        except Exception as e:
            if logger and debug:
                msg = '"Error copying file"'
                logger.debug(msg)
                logger.debug(e)
        files_not_copied = len([e for e in src_files if not e[1]]) > 0
        if files_not_copied:
            if logger and debug:
                retry_in = wait_interval
                files_left = len([e for e in src_files if not e[1]])
                msg = ('Not all files copied. {0} files left. Retrying in {1} '
                       'seconds. This is the {2} attempt.')
                msg = msg.format(files_left,retry_in,attempts)
                logger.debug(msg)
            time.sleep(wait_interval)
    if files_not_copied:
        files_left = len([e for e in src_files if not e[1]])
        files_copied = len([e for e in src_files if e[1]])
        files_total = len(src_files)
        if (attempts >= max_retries):
            err_msg = ('Transfer of files between {0} and {1} timed out. '
                       '{2} out of {3} files copied. {4} missing.')
            err_msg.format(source,dest_dir,files_copied,files_total,files_left)
            raise errors.TransferTimedOut(err_msg)
        else:
            err_msg = ('Not all files copied between {0} and {1}. '
                       '{2} out of {3} files copied. {4} missing.')
            err_msg.format(source,dest_dir,files_copied,files_total,files_left)
            raise errors.TransferError(err_msg)
    if transit:
        if logger and debug:
            msg = ('Moving the folder {0} (in transit folder) to final '
                   'destination folder {1}')
            msg.format(dest_dir,dest)
            logger.debug(msg)
        shutil.move(dest_dir,dest)
    if delete_original: 
        if logger and debug:
            msg = ('Deleting source files in {0}.'.format(source))
            logger.debug(msg)
        shutil.rmtree(source)
    msg = ('All files have been copied from {0} to {1}.')
    msg.format(source,dest_dir)
    logger.debug(msg) 

def cutPdf(inputPdf, outputPdf, fromPage, toPage):
    '''
    Wrapper around pdftk - create outputPdf from the range
    specified in from, to based on inputPdf
    will return false if exit code is not 0 (i.e. an error code)
    '''
    page_range = "{0}-{1}".format(fromPage, toPage)
    exit_code = subprocess.call(['pdftk', inputPdf, 'cat', page_range, 'output', outputPdf])
    
    return exit_code == 0

def convertLangToLocale(code):
    '''
    TODO - Clarify this with Jeppe
    Need to map between lang codes supplied
    by Goobi (ISO 639-1?) e.g. da
    and the locale codes that OJS needs, e.g. da_DK
    For now we'll just use a placeholder
    '''
    try:
        return {
            'da': 'da_DK',
            'en': 'en_US'
        }[code]
    except: 
        return ''



def parseTitle(title):
    '''
    Given a title, return the first 10 characters
    Used when journal titles determine path names,
    e.g. OJS import.
    TODO: Make sure all references to journal titles
    use this method.
    '''
    return title[0:10]
