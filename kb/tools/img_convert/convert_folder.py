'''
Created on 19/06/2014

@author: jeel
'''

import os

import time
import sys

# I dont like it, http://stackoverflow.com/a/4284378
lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../../')
sys.path.append(lib_path)
#print lib_path
import tools.tools as tools
from tools.processing import processing

class ConvertError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def convert_folder(input_folder, output_folder,quality=50,resize_type='width',
                   resize=700,input_ext='tif',output_ext='jpeg'):
    '''
    TODO: document
    default resize is the desired width of the output image. Height will be
    set to keep aspect ratio
    '''
    images = sorted([f for f in os.listdir(input_folder) if f.endswith(input_ext)])
    image_jobs = set()
    index = 1
    for image in images:
        input_path = os.path.join(input_folder,image)
        #output_file_name = input_folder_name+'-'+str(index).zfill(8)+'.'+output_ext
        output_file_name = str(index).zfill(8)+'.'+output_ext
        output_path = os.path.join(output_folder,output_file_name)
        if not os.path.exists(output_path): # Skip file if already exist
            image_jobs.add((input_path,output_path,quality,resize_type,resize))
        index += 1
    # Ready for multithreading - notice that im and gm is multithreaded.
    return tools.get_delta_time(convert_images(image_jobs))

def convert_images(image_jobs):
    results = [] #proc_time,output
    start = time.time()
    for input_path,output_path,quality,resize_type,resize in image_jobs:
        if resize_type == 'width':
            cmd = 'gm convert {0} -quality {1}% -resize {2} {3}'
        else: # resize by percentage
            cmd = 'gm convert {0} -quality {1}% -resize {2}% {3}'
        cmd = cmd.format(input_path,quality,resize,output_path)
        proc_start_time = time.time()
        result = processing.run_cmd(cmd,shell=True,print_output=False,raise_errors=False)
        if result['erred']:
            err = ('An error occured when converting files with command {0}. '
                   'Error: {1}.')
            err = err.format(cmd,result['output'])
            raise ConvertError(err)
        proc_time = time.time() - proc_start_time
        results.append((proc_time,result))
    total_proc_time = time.time()-start
    return total_proc_time

def split_set_equally(input_set, chunks=2):
    #http://enginepewpew.blogspot.dk/2012/03/splitting-dictionary-into-equal-chunks.html
    return_list = [set() for idx in xrange(chunks)]
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
        convert_folder(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])
