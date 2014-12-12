#!/usr/bin/env python
# -*- coding: utf-8


'''
Created on 11/12/2014

@author: jeel
'''
import os
from tools.processing import processing

def mergePdfFilesInFolder(input_folder,pdf_dest):
    '''
    Merges all the pdf-files in a folder and outputs to a specified path
    '''
    src = os.path.join(input_folder,'*.pdf')
    cmd = 'pdftk {0} cat output {1}'.format(src,pdf_dest)
    processing.run_cmd(cmd,shell=True)
    
def joinPdfFiles(pdf_list,dest_path):
    '''
    Adds a list of pdf-files in front of a master pdf. It creates a new temp
    pdf in the temp_folder and if everything goes right, it overwrites the
    master with the outputted pdf-file.
    '''
    if len(pdf_list) == 0:
        raise ValueError('No pdf files to join')
    # Make sure that all pdf-files exists
    for pdf in pdf_list:
        if not os.path.exists(pdf):
            raise OSError('{0} does not exists.'.format(pdf))
    pdfs = ' '.join(pdf_list)
    cmd = 'pdftk {0} cat output {1}'.format(pdfs, dest_path)
    output = processing.run_cmd(cmd,shell=True)
    if output['erred'] or 'error' in output['stdout']:
        raise OSError('An error occured when converting files to pdf with ' 
                      'command {0}. Error: {1}.'.format(cmd,output))
