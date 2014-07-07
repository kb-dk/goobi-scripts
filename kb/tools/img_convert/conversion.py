'''
Created on 06/07/2014

@author: jeel
'''
import os


from kb.tools.processing import processing


def convert_to_bitonal(image_path,output_path,
                       use_optimize2bw = False,
                       optimize2bw_thresshold = 0):
    '''
    Creates a bitonal tif-file with Group4 compression from an input image.
    Use either GraphicMagicks' convert or ExtactImage's optimize2bw.
    
    optimize2bw will generally give an image with thinner characters than
    GM's convert. Thus optimize2bw may be preferred to ink printed text.  
    
    '''    
    if use_optimize2bw:
        if not optimize2bw_thresshold == 0: 
            cmd = 'optimize2bw -t {0} -i {1} -o {2}'
            cmd = cmd.format(optimize2bw_thresshold,image_path,output_path)
        else:
            cmd = 'optimize2bw -i {0} -o {1}'
            cmd = cmd.format(image_path,output_path)
    else:
        convert_options = '-threshold 75% -monochrome -compress Group4'
        cmd = 'gm convert {0} {1} {2}'
        cmd = cmd.format(image_path, convert_options,output_path)
    processing.run_cmd(cmd,shell=True)
    
def extract_illustrations(image_name, coordinates,output_folder,
                          text_background_path, illustration_size_limit = 50,
                          text_background_quality=90,
                          extract_quality=50,extract_resize=25,
                          hori_ratio=0.01, vert_ratio=25,logger=None):
    '''
    TODO: Add documentation.
    '''
    
    crop_cmd = 'gm convert '+image_name+' '
    illustrations = {}
    ill_index = 0
    for coordinate in coordinates:
        bbox = coordinate.replace(' ','_')
        coordinate = [c for c in coordinate.split() if c.isdigit()]
        if not len(coordinate) == 4:
            if logger:
                msg = ('Bbox coordinates "{0}" not valid. Bbox coordinate list '
                       'must contain four digits, e.g "bbox 612 301 2433 418"')
                msg = msg.format(coordinate)
                logger.debug(msg)
            continue
        # nw = north west, se = south east
        x_nw = int(coordinate[0])
        y_nw = int(coordinate[1])
        x_se = int(coordinate[2])
        y_se = int(coordinate[3])
        width = x_se-x_nw
        height = y_se-y_nw
        if (width == 0 or height == 0):
            msg = ('The coordinates {0} results in a width or height equals 0. '
                   'Width {1}) and height {2} must be larger than 0. File: {3}')
            msg = msg.format(coordinate,width,height,image_name)
            if logger: logger.debug(msg)
            continue
        
        if width < illustration_size_limit and height < illustration_size_limit:
            if logger:
                msg = ('The coordinates {0} results in a to to small image. '
                       'Width ({1}) and height ({2}) must be larger than {3}.')
                msg = msg.format(coordinate,width,height,illustration_size_limit)
                #logger.debug(msg)
            continue
        ratio = float(width)/float(height)
        if not (hori_ratio < ratio < vert_ratio):
            if logger:
                msg = ('The coordinates {0} results in a to thin image. '
                       'Ratio must be between {1} and {2}, but is {3}')
                msg = msg.format(coordinate,hori_ratio,vert_ratio,ratio)
                #logger.debug(msg)
            continue
        output_file_name = str(ill_index)+'_{0}x{1}+{2}+{3}_{4}.jpg'
        output_file_name = output_file_name.format(width,height,x_nw,y_nw,bbox)
        output_file_path = os.path.join(output_folder,output_file_name)
        output_settings = '-crop {0}x{1}+{2}+{3} -quality {4}% -resize {5}%'
        output_settings = output_settings.format(width,height,x_nw,y_nw,
                                                 extract_quality,extract_resize)
        cmd = ('gm convert {0} {1} "{2}"')
        cmd = cmd.format(image_name,output_settings,output_file_path)
        processing.run_cmd(cmd,True)
        illustrations[ill_index] = {'x_nw': x_nw,
                                    'y_nw': y_nw,
                                    'x_se': x_se,
                                    'y_se': y_se,
                                    'width': width,
                                    'height': height,
                                    'file_path': output_file_path,
                                    }
        # add options to remove region convert command 
        output_settings = ' -region {0}x{1}+{2}+{3} -fill white -colorize 100%'
        output_settings = output_settings.format(width,height,x_nw,y_nw)
        crop_cmd += output_settings
        ill_index += 1
    crop_cmd += ' -quality {0}% {1}'
    crop_cmd = crop_cmd.format(text_background_quality,text_background_path) 
    processing.run_cmd(crop_cmd,True)
    return  illustrations