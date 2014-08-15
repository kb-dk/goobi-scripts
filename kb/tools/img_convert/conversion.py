'''
Created on 06/07/2014

@author: jeel
'''
import os
import sys
import shutil
import time
lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../../')
sys.path.append(lib_path)
from tools.filesystem import fs
from tools.processing import processing


def convert_to_bitonal(image_path,output_path,
                       use_optimize2bw = False,
                       threshold = None):
    '''
    Creates a bitonal tif-file with Group4 compression from an input image.
    Use either GraphicMagicks' convert or ExtactImage's optimize2bw.
    
    optimize2bw will generally give an image with thinner characters than
    GM's convert. Thus optimize2bw may be preferred to ink printed text.  
    
    '''    
    if use_optimize2bw:
        if not threshold is None: 
            cmd = 'optimize2bw -t {0} -i {1} -o {2}'
            cmd = cmd.format(threshold,image_path,output_path)
        else:
            cmd = 'optimize2bw -i {0} -o {1}'
            cmd = cmd.format(image_path,output_path)
    else:
        if not threshold is None: 
            threshold = int((threshold/255.0)*100) # convert to pct
            convert_options = '-threshold {0}% -monochrome -compress Group4'
            convert_options = convert_options.format(threshold)
            cmd = 'gm convert {0} {1} {2}'
            cmd = cmd.format(image_path, convert_options,output_path)
        else:
            convert_options = '-threshold 75% -monochrome -compress Group4'
            cmd = 'gm convert {0} {1} {2}'
            cmd = cmd.format(image_path, convert_options,output_path)
    processing.run_cmd(cmd,shell=True)
    
def extract_illustrations(image_path, illustrations,output_folder,
                          text_background_path, text_background_quality=90,
                          extract_quality=50,extract_resize=25,logger=None):
    '''
    TODO: Add documentation.
    '''
    
    crop_cmd = 'gm convert '+image_path+' '
    accepted_illustrations = []
    for illustration in illustrations:
        x_nw = illustration['x_nw']
        y_nw = illustration['y_nw']
        x_se = illustration['x_se']
        y_se = illustration['y_se']
        width = illustration['width']
        height = illustration['height']
        height = y_se-y_nw
        file_path = '{0}x{1}+xnw_{2}+ynw_{3}+xse_{4}+yse_{5}.jpg'
        file_path = file_path.format(width,height,x_nw,y_nw,x_se,y_se)
        file_path = os.path.join(output_folder,file_path)
        settings = '-crop {0}x{1}+{2}+{3} -quality {4}% -resize {5}%'
        settings = settings.format(width,height,x_nw,y_nw,extract_quality,extract_resize)
        cmd = ('gm convert {0} {1} "{2}"')
        cmd = cmd.format(image_path,settings,file_path)
        processing.run_cmd(cmd,True)
        illustration['file_path']=file_path
        accepted_illustrations.append(illustration)
        # add options to remove region convert command 
        settings = ' -region {0}x{1}+{2}+{3} -fill white -colorize 100%'
        settings = settings.format(width,height,x_nw,y_nw)
        crop_cmd += settings
    crop_cmd += ' -quality {0}% {1}'
    crop_cmd = crop_cmd.format(text_background_quality,text_background_path) 
    processing.run_cmd(crop_cmd,True)
    return accepted_illustrations

def select_illustrations(images, threshold_abs = 127, accept_bw_ratio=25.0,
                         output_dest=None):
    '''
    Perform a bw-test on all illustrations, where the ratio between
    black and white pixels in a monochrome version of the image is matched
    with "accept_bw_ratio" -> if higher, the .
    
    output "illustrations" will be the accepted illustrations from the
    test.
    
    Use "bw_ratio_dest" to copy the illustrations into the folder
    "bw_ratio_dest" with % amount of black pixels as prefix in file name.
    '''
    accepted_illustrations = {}
    if (output_dest is not None and not os.path.isdir(output_dest)):
        try:
            fs.createFolderIfParentExist(output_dest)
        except:
            output_dest = None
    threshold_rel = int((threshold_abs/255.0*100))
    cmd = (' convert {0} -threshold {1}% -monochrome miff:- '
           '| convert - -format "%[fx:mean]" info:')
    for key,val in images.items():
        image = val['file_path']
        image_basename = os.path.basename(image)
        tmp_cmd = cmd.format(image,threshold_rel)
        result = processing.run_cmd(tmp_cmd,shell=True)
        pct_black = round(100-(float(result['stdout'].strip())*100),2)
        #msg = '{0}% of black pixels for {1} with threshold {2}'
        #msg = msg.format(pct_black,image_basename,threshold_rel)
        #print(msg)
        if output_dest is not None:
            output_name = str(pct_black)+'---'+image_basename
            output_copy_path = os.path.join(output_dest,output_name)
            shutil.copy(image, output_copy_path)
        if pct_black > accept_bw_ratio:
            accepted_illustrations[key] = val
    return accepted_illustrations

if __name__ == '__main__':
    src = sys.argv[1]
    images = dict()
    for f in os.listdir(src):
        if os.path.isfile(os.path.join(src,f)):
            images[f] = {'file_path':os.path.join(src,f)}
    result = select_illustrations(images,
                                  threshold_abs = int(sys.argv[2]),
                                  output_dest='/home/jew/bw_ratio_test/test_results2/')
    
    