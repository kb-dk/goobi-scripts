#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 11/12/2014

@author: jeel
'''
import os
from tools.processing import processing


class ConvertError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class InnerCropError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def innercrop(src,dest_folder,w,h,innercrop_path,mode='box',fuzzval=75):
    '''
    Returns the crop coordinates for src as a dictionary together with 
    a path to a cropped version of src.
    
    Uses "innercrop" from Fred's ImageMagick Scripts to get coordinates for
    cropping the image. "innercrop" also outputs a cropped image file.
    
    http://www.fmwconcepts.com/imagemagick/innercrop/index.php
    '''
    file_name,ext = os.path.splitext(os.path.basename(src))
    if mode == 'box':
        dest = os.path.join(dest_folder,file_name+'_innercrop.jpg')
    else:
        dest = os.path.join(dest_folder,file_name+'_innercrop'+ext)
    cmd = '{0} -f {1} -m {2} {3} {4}'
    cmd = cmd.format(innercrop_path,fuzzval,mode,src,dest)
    output = processing.run_cmd(cmd,shell=True)
    if output['erred'] or 'error' in str(output['stderr']).lower():
        raise InnerCropError(output['stderr'].decode("utf-8"))
    coordinates = getInnercropCoordinates(output['stdout'],w,h)
    return dest,coordinates

def getInnercropCoordinates(output,w,h):
    '''
    Returns a dictionary with cropping information from the output from 
    "innercrop"
    
    '''
    nw_word = 'Upper Left Corner: '
    se_word = 'Lower Right Corner: '
    retval = {'r_crop':0,
              'l_crop':0,
              't_crop':0,
              'b_crop':0}
    output = str(output)
    if nw_word in output:
        nw_start = output.find(nw_word)+len(nw_word)
        nw_end = output.find('\\n',output.find(nw_word))
        nw_x,nw_y = list(map(lambda x: int(x), output[nw_start:nw_end].split(',')))
        retval['nw_x'] = nw_x
        retval['l_crop'] = nw_x
        retval['nw_y'] = nw_y
        retval['t_crop'] = nw_y
    if se_word in output:
        se_start = output.find(se_word)+len(se_word)
        se_end = output.find('\\n',output.find(se_word))
        se_x,se_y = map(lambda x: int(x), output[se_start:se_end].split(','))
        retval['se_x'] = se_x
        retval['r_crop'] = w-se_x
        retval['se_y'] = se_y
        retval['b_crop'] = h-se_y
    return retval

def convertToBw(src,dest,threshold=10):
    '''
    Converts src to a bitonal tif-file compressed with Group4
    
    '''
    cmd = 'convert {0} -threshold {1}% -compress Group4 {2}'
    cmd = cmd.format(src,threshold,dest)
    processing.run_cmd(cmd,shell=True)
    return dest
        
def cropImage(src,dest_folder,info,dest=None,to_tif=False):
    '''
    Crops src and outputs it to dest_folder.
    
    :param src:
    :param dest_folder:
    :param info: contains the coordinates for cropping 
    :param dest:
    :param to_tif:
    '''
    coordinates = info['crop_coordinates']
    w = info['image_width']
    h = info['image_height']
    file_name = os.path.basename(src)
    file_name,ext = os.path.splitext(file_name)
    if dest is None: dest = os.path.join(dest_folder,file_name+'_cropped'+ext)
    nw_x = coordinates['nw_x'] if info['l_crop'] else 0
    nw_y = coordinates['nw_y'] if info['t_crop'] else 0
    se_x = coordinates['se_x'] if info['r_crop'] else w
    se_y = coordinates['se_y'] if info['b_crop'] else h
    width = se_x-nw_x
    height = se_y-nw_y
    to_tif = '-threshold 60% -compress Group4' if to_tif else ''
    settings = '-crop {0}x{1}+{2}+{3}'.format(width,height,nw_x,nw_y)
    cmd = 'convert {0} {1} {2} {3}'.format(src,settings,to_tif,dest)
    processing.run_cmd(cmd,shell=True)
    return dest

def deskewImage(src,dest_folder,angle,quality=None,resize=None):
    '''
    Deskews an image with a given angle.
    
    :param src: path to image to deskew
    :param dest_folder: where to output deskewed image
    :param angle: what to deskew image with
    :param quality: what to compress output image with
    :param resize: what to resize output image with (pct)
    '''
    file_name,ext = os.path.splitext(os.path.basename(src))
    dest = os.path.join(dest_folder,file_name+'deskewed'+ext)
    if quality is not None:
        quality = '-quality {0}%'.format(quality)
    else:
        quality = ''
    if resize is not None:
        resize = '-resize {0}%'.format(resize)
    else:
        resize = ''
    cmd = 'convert {0} -rotate {1} {2} {3} {4}'.format(src,angle,resize,quality,dest)
    processing.run_cmd(cmd,shell=True)
    return dest

def compressFile(input_file,output_file,quality=50,resize=None,resize_type='pct'):
    if resize is not None:
        if resize_type == 'width':
            resize = '-resize {0}'.format(resize)
        else: # resize by percentage
            resize = '-resize {0}%'.format(resize)
    else:
        resize = ''
    cmd = 'gm convert {0} {1} -quality {2} {3}'.format(input_file,resize,quality,output_file)
    result = processing.run_cmd(cmd,shell=True,print_output=False,raise_errors=False)
    if result['erred']:
        err = ('An error occured when converting files with command {0}. '
               'Error: {1}.')
        err = err.format(cmd,result['output'])
        raise ConvertError(err)

def getDeskewAngle(src,threshold=75):
    cmd = "convert {0} -deskew {1} -format '%[deskew:angle]' info:".format(src,threshold)
    output = processing.run_cmd(cmd,shell=True)
    return float(output['stdout'])

def getImageDimensions(image_path,hocr=None):
    '''
    Todo: document this
    '''
    try:
        # Use identify instead
        cmd = 'identify {0}'.format(image_path)
        identify_info = processing.run_cmd(cmd = cmd,shell=True,print_output = False)
        size = str(identify_info['stdout']).split()[2].split('x')
    except Exception as e:
        # Ye, I know
        raise e
    width, height = int(size[0]),int(size[1])
    return width, height