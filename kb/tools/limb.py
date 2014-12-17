#!/usr/bin/env python
# -*- coding: utf-8

import tools.tools as tools
from tools.errors import DataError
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

def altoFileCountMatches(alto_dir, input_files_dir,valid_exts):
    '''
    Ensure number of alto files is the same as the
    number of input files.
    Return boolean
    '''
    numAlto = len(os.listdir(alto_dir))
    numInputFiles = tools.getFileCountWithExtension(input_files_dir,valid_exts)

    return numAlto == numInputFiles

def pageCountMatches(pdf_input_dir,input_files_dir,valid_exts):
    '''
    Compare num pages in pdfinfo with pages in input 
    picture directory. 
    return boolean 
    '''
    pdf = tools.getFirstFileWithExtension(pdf_input_dir, '.pdf')
    pdfInfo = tools.pdfinfo(os.path.join(pdf_input_dir, pdf))
    numPages = int(pdfInfo['Pages'])
    numInputFiles = tools.getFileCountWithExtension(input_files_dir,valid_exts)
    return numPages == numInputFiles

def alreadyMoved(toc_dir,pdf_input_dir,input_files_dir,alto_dir,valid_exts):
    '''
    Validate that the following files are present and valid
    :param toc_dir:
    :param pdf_input_dir:
    :param input_files_dir:
    :param alto_dir:
    :param valid_exts:
    '''
    
    try:
        performValidations(toc_dir,
                           pdf_input_dir,
                           input_files_dir,
                           alto_dir,
                           valid_exts)
    except DataError:
        return False
    return True

def performValidations(toc_dir,pdf_input_dir,input_files_dir,alto_dir,valid_exts):
    '''
    1: validering af pdf (antal sider i pdf == antal input billeder)
    2: validering af toc-fil (pt. er der en fil - validering ved parsing efterfoelgende)
    3: validering af alto-filer (evt. "er der lige saa mange som input billeder" eller "er der filer")
    
    Throw DataError if any validation fails
    '''
    if not tocExists(toc_dir): 
        raise DataError("TOC not found!")
    if not pageCountMatches(pdf_input_dir,input_files_dir,valid_exts):
        raise DataError("PDF page count does not match input picture count!")
    if not altoFileCountMatches(alto_dir, input_files_dir,valid_exts):
        raise DataError("Number of alto files does not match number of input files.")
    