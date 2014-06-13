'''
Created on 13/06/2014

@author: jeel
'''
import os
import filecmp

def compareDirectories(src,dest):
    
    checkDirectoriesExist(src,dest)
    return _compareDirectories(src,dest)

def _compareDirectories(dir1, dir2):
    """
    From: http://stackoverflow.com/a/6681395
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.
    
    @param dir1: First directory path
    @param dir2: Second directory path
    
    @return: True if the directory trees are the same and 
        there were no errors while accessing the directories or files, 
        False otherwise.
    """
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if len(dirs_cmp.left_only)>0 or len(dirs_cmp.right_only)>0 or \
        len(dirs_cmp.funny_files)>0:
        return False
    (_, mismatch, errors) =  filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch)>0 or len(errors)>0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not _compareDirectories(new_dir1, new_dir2):
                return False
    return True

    
def checkDirectoriesExist(*args):
    """
    Given a variable number of directories
    return false if any of them do not exist
    """
    for directory in args:
        checkDirectory(directory)
    return True

def checkDirectory(directory):
    if not directory:
        raise NameError('Argument "directory" not set.')
    elif not os.path.exists( directory ) :
        error = 'Directory "{0}" does not exist.'
        error = error.format(directory)
        raise IOError(error)
    else:
        if not os.path.isdir( directory ) :
            error = '"{0}" is not a directory.'
            error = error.format(directory)
            raise IOError(error)
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