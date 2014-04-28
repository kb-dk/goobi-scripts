#!/usr/bin/python

'''
Created on 26/03/2014

@author: jeel
'''


import os
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


# Given a folder path, check to see 
# if folder exists or create it
# return true if successful
# false if folder could not be created
def find_or_create_dir(path):
    if os.path.exists(path) and os.path.isdir(path):
        return True
    else:
        try:
            os.makedirs(path)
            return True
        except IOError as e:
            return False, e.strerror


def move_file(file_path,dest_folder,logger=None):
    '''Moves a file from file_path to dest_folder.
    Checks paths and logs errors.
    '''
    error = check_file(file_path)
    if error: 
        if logger: logger.error(error)
        return error
    error = check_folder(dest_folder)
    if error:
        if logger: logger.error(error)
        return error
    try:
        '''
        shutil.move doc:
        "If the destination is on the current filesystem, then os.rename() is 
        used. Otherwise, src is copied (using shutil.copy2()) to dst and then 
        removed."
        '''
        shutil.move(file_path, dest_folder)
        msg = 'File '+file_path+'moved corretly to '+dest_folder
        if logger: logger.info(msg)
    except Exception as e:
        error = 'An error occured when copying '+file_path+' to '+dest_folder+\
            '. Error msg:'+e.strerror
        if logger: logger.error(error)
        
    return error

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
    error = None
    if not file_path:
        error = 'Argument "file_path" not set.' 
    elif not os.path.exists( file_path ) :
        error = 'File "' + file_path + '" does not exist.'
    else:
        if not os.path.isfile( file_path ) :
            error = 'File "' + file_path + '" is not a file_path.'
        else:
            try:
                with open( file_path ) : pass
            except IOError:
                error = 'File "' + file_path + '" exists but unable to open it.'
    return error

def check_folder(folder):
    error = None
    if not folder:
        error = 'Argument "folder" not set.'
    elif not os.path.exists( folder ) :
        error = 'Folder "' + folder + '" does not exist.'
    else:
        if not os.path.isdir( folder ) :
            error = 'Folder "' + folder + '" is not a folder.'
    return error

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