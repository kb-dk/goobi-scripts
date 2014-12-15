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

def createPdfFromFolder(src, file_dest,temp_folder,
                        quality=50,resize_pct=50,valid_exts=['jpg','tif']):
    '''
    Use ImageMagick to create one pdf from all the images in a folder and 
    output to a given destination.
    
    Create a pdf of each image and place in temp folder. Merge output pdf-files
    to pdf-dest and remove temp folder.
    
    '''
    image_paths = sorted([f for f in os.listdir(src)
                     if os.path.splitext(f)[1].lstrip('.') in valid_exts])
    for image in image_paths:
        input_path = os.path.join(src,image)
        file_name,_ = os.path.splitext(image)
        output_file_name = file_name+'.pdf'
        output_path = os.path.join(temp_folder,output_file_name)
        image_tools.compressFile(input_path, output_path, quality, resize_pct)
    pdf_misc.mergePdfFilesInFolder(temp_folder,file_dest)
    fs.clear_folder(temp_folder,also_folder=True)

def convertFolder(input_folder, output_folder,quality=50,resize_type='width',
                   resize=700,valid_exts=['tif','jpg']):
    '''
    Resizes and compresses images in a folder to jpegs in another folder. Used
    to create thumbnails. 
    
    The method is used to create thumbnails for Goobi. As KBs Boobi is 
    configured to only look for images of the form NNNNNNN.jpg, images are named
    after this sequence.
    
    :param input_folder: Folder containing images to convert
    :param output_folder: Destination folder
    :param quality: % to compress output jpeg as
    :param resize_type: Resize by percentage or width. Default resize is the 
        desired width of the output image. Height will be set to keep aspect 
        ratio
    :param resize: the height or percentage to resize after.
    :param valid_exts: Only convert images with extensions in this list
    '''
    images = sorted([f for f in os.listdir(input_folder)
                     if os.path.splitext(f)[-1].lstrip('.') in valid_exts])
    for index, image in enumerate(images):
        input_path = os.path.join(input_folder,image)
        output_file_name = str(index).zfill(8)+'.jpg'
        output_path = os.path.join(output_folder,output_file_name)
        image_tools.compressFile(input_path,output_path,quality,resize,resize_type)

   
if __name__ == '__main__':
    if not len(sys.argv) == 7:
        print("Usage: %s <input_folder> <output_folder> <quality> <resize-type> <resize> <input-ext>\n" 
              % os.path.basename(sys.argv[0]))
    else:
        convertFolder(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])
