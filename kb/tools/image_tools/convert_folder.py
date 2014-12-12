#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 19/06/2014

@author: jeel
'''

import os
import time
import sys

import tools.tools as tools
from tools.processing import processing
from tools.filesystem import fs
from tools.pdf import misc as pdf_misc
from tools.image_tools import misc as image_tools

def createPdfFromFolder(input_folder, file_destination,temp_folder_root, 
                        quality=50,resize_pct=50,valid_exts=['jpg','tif']):
    '''
    Use ImageMagick to create one pdf from all the images in a folder and 
    output to a given destination.
    
    Create a pdf of each image and place in temp folder. Merge output pdf-files
    to pdf-dest and remove temp folder.
    
    '''
    folder_name = os.path.basename(input_folder.rstrip(os.sep))
    temp_folder = os.path.join(temp_folder_root,folder_name)
    images = sorted([f for f in os.listdir(input_folder)
                     if os.path.splitext(f)[1] in valid_exts])
    t = time.time()
    for image in images:
        input_path = os.path.join(input_folder,image)
        file_name,_ = os.path.splitext(image)
        output_file_name = file_name+'.pdf'
        output_path = os.path.join(temp_folder,output_file_name)
        image_tools.compressFile(input_path, output_path, quality, resize_pct)
    pdf_misc.mergePdfFilesInFolder(temp_folder,file_destination)
    fs.clear_folder(temp_folder,also_folder=True)
    dt = time.time()-t  
    print('Time used to create a pdf from {0}: {1}'.format(folder_name,tools.get_delta_time(dt)))
        

def convertFolder(input_folder, output_folder,quality=50,resize_type='width',
                   resize=700,input_ext='tif',output_ext='jpeg'):
    '''
    TODO: document
    default resize is the desired width of the output image. Height will be
    set to keep aspect ratio
    '''
    images = sorted([f for f in os.listdir(input_folder) if f.endswith(input_ext)])
    for index, image in enumerate(images):
        input_path = os.path.join(input_folder,image)
        #file_name,_ = os.path.splitext(image)
        #output_file_name = file_name+'.'+output_ext
        output_file_name = str(index).zfill(8)+'.'+output_ext
        output_path = os.path.join(output_folder,output_file_name)
        image_tools.compressFile(input_path,output_path,quality,resize,resize_type)


def splitSetEqually(input_set, chunks=2):
    #http://enginepewpew.blogspot.dk/2012/03/splitting-dictionary-into-equal-chunks.html
    return_list = [set() for idx in range(chunks)]
    idx = 0
    for elem in input_set:
        return_list[idx].add(elem)
        if idx < chunks-1: # indexes start at 0
            idx += 1
        else:
            idx = 0
    return return_list

   
if __name__ == '__main__':
    if not len(sys.argv) == 7:
        print("Usage: %s <input_folder> <output_folder> <quality> <resize-type> <resize> <input-ext>\n" 
              % os.path.basename(sys.argv[0]))
    else:
        convertFolder(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])
