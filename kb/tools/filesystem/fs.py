#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 13/06/2014

@author: jeel
'''
import os
import filecmp


def clear_folder(path,also_folder=False,ignore_exceptions=True):
    '''
    Deletes all the files in a folder specified by "path". If specified by
    "also_folder", also delete the folder given by "path".
    '''
    if not os.path.isdir(path):
        if ignore_exceptions:
            return
        error = '{0} is not a valid folder.'
        error = error.format(path)
        raise IOError(error)
    for c in os.listdir(path):
        c = os.path.join(path,c)
        if os.path.isdir(c) and len(os.listdir(c)) == 0:
            os.rmdir(path)
        elif os.path.isfile(c):
            os.remove(c)
    if also_folder and len(os.listdir(path)) == 0:
        os.rmdir(path)

def find_or_create_dir(*paths):
    '''
    Given a folder path, check to see 
    if folder exists or create it
    Raises exception in case of error
    '''
    for path in paths:
        if os.path.exists(path):
            if not os.path.isdir(path):
                error = '{0} is not a valid directory.'.format(path)
                raise IOError(error)
        elif not os.path.exists(path):
            os.makedirs(path)

def detectImagesExts(folder,valid_exts):
    images = [f for f in os.listdir(folder)
              if f.split('.')[-1] in valid_exts]
    ext = ''
    for image in images:
        img_ext = image.split('.')[-1]
        if (not ext == '') and (not img_ext == ext):
            raise ValueError('Multiple image extension in master folder not allowed.')
        else:
            ext = img_ext
    if not ext == '':
        return ext
    else:
        raise ValueError('No image file extensions found in master image folder.')

def folderExists(folder):
    return os.path.isdir(folder)

def folderWritable(folder):
    return os.access(folder, os.W_OK)

def getParentFolder(folder):
    return os.path.dirname(folder)
    
def createFolderIfParentExist(folder):
    parent_folder = getParentFolder(folder)
    if not os.path.exists(folder):
        if os.path.exists(parent_folder):
            os.mkdir(folder)
        else:
            err = ('Parent folder ({0}) to log folder {1} does not exist.')
            err = err.format(parent_folder,folder)
            raise IOError(err)

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

    

def getFileSize(path,mb=True):
    size = int(os.stat(path).st_size)
    if mb:
        return round(float(size)/float(1024*1024),2)
    else:
        return round(size,2)
    
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
    if not path:
        raise IOError('Argument "path" not set.')
    elif not os.path.exists(path):
        os.makedirs(path)