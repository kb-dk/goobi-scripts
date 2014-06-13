'''
Created on 01/06/2014

@author: jeel
'''

import json
import os

def create_convert_options(path,default_options):
    '''
    
    '''
    image_ext = default_options['image_ext'].split(';')
    prefix_zeros = int(default_options['prefix_zeros'])
    images = [f for f in os.listdir(path)
              if f.split('.').pop() in (image_ext)]
    if not len(images):
        error = ('Image folder {0} has no files with file extension {1}.')
        error = error.format(path,', '.join(image_ext))
        raise IOError(error)
    images.sort()
    options = dict()
    for i in range(len(images)):
        rel_path = images[i]
        abs_path = os.path.join(path,rel_path)
        filesize = int(os.stat(abs_path).st_size)
        new_entry = {'path': abs_path,
                     'filename':rel_path,
                     'color': default_options['color'],
                     'jpeg_quality': default_options['jpeg_quality'],
                     'bitonal_resize': default_options['bitonal_resize'],
                     'grayscale_resize': default_options['grayscale_resize'],
                     'color_resize': default_options['color_resize'],
                     'filesize': filesize,
                     'density': default_options['density'],
                     'deviation_from_median': None,
                     'deviation_from_avg_size': None
                    }
        key = str(i).zfill(prefix_zeros)
        options[key] = new_entry
    # Calculate median, avg. and total file size
    if default_options['color_detection']:
        mean = calculate_mean(options)
        avg_size = calculate_avg_size(options)
        total_size = calculate_total_size(options)
        default_options['median_file_size'] = mean
        default_options['avg_file_size'] = avg_size
        default_options['total_ebook_size'] = total_size
        # Set color selection for each image
        options = detect_colors(options,default_options,mean,avg_size)
    # Add conversion default_options for Image Magick
    options = set_convert_options(options)
    return options

def set_convert_options(options):
    '''
    Set the options needed for conversion with ImageMagics Convert
    '''
    for key in options:
        # TODO: Some of these should be set be user when adding files to process
        entry = options[key]
        density = entry['density']
        bitonal_resize = entry['bitonal_resize']
        color_resize = entry['color_resize']
        grayscale_resize = entry['grayscale_resize']
        jpeg_quality = entry['jpeg_quality']
        color = entry['color']
        co = ''  # convert_options
        if color == 'bitonal':
            co += '-threshold 75% -monochrome -compress Group4'
            if not bitonal_resize == 100:
                co += ('-resize {0}% -units PixelsPerInch -density {1}')
                co = co.format(str(bitonal_resize),
                               str(density * (float(bitonal_resize) / 100.0))
                               ) 
        elif color == 'grayscale':
            co += ('-type Grayscale -resize {0}% -quality {1}% '
                   '-units PixelsPerInch -density {2}')
            co = co.format(str(grayscale_resize),
                           str(jpeg_quality),
                           str(density * (float(grayscale_resize) / 100.0))
                           )
        elif color == 'color':
            co += ('-resize {0}% -quality {1}% '
                   '-units PixelsPerInch -density {2}')
            co = co.format(str(color_resize),
                           str(jpeg_quality),
                           str(density * (float(color_resize) / 100.0)))
        options[key]['convert_options'] = co
    return options

def detect_colors(options,default_options, median, avg_size):
    '''
    
    '''
    
    for key in options:
        file_size = options[key]['filesize']
        deviation_from_median = \
            round((float(file_size) / float(median)) * 100, 2)
        deviation_from_avg_size = \
            round((float(file_size) / float(avg_size)) * 100, 2)
        options[key]['deviation_from_median'] = deviation_from_median
        options[key]['deviation_from_avg_size'] = deviation_from_avg_size
        if (deviation_from_median > 
            default_options['color_detection_color_limit']):
            options[key]['color'] = 'color'
        elif (deviation_from_median > 
              default_options['color_detection_grayscale_limit']):
            options[key]['color'] = 'grayscale'
    return options

def calculate_total_size(options):
    '''
    '''
    file_sizes = [options[f]['filesize'] \
                  for f in options]
    return sum(file_sizes)

def calculate_mean(options):
    '''
    '''
    file_sizes = [options[f]['filesize'] \
                  for f in options]
    file_sizes.sort()
    return file_sizes[int(len(file_sizes) / 2)]

def calculate_avg_size(options):
    '''
    '''
    file_sizes = [options[f]['filesize'] \
                  for f in options]
    total_size = sum(file_sizes)
    file_count = len(file_sizes)
    return total_size / file_count

def load_json_file(path):
    '''
    '''
    if not os.path.exists(path) or not os.path.isfile(path):
        error = 'The file {0} does not exist.'
        error.format(path)
        raise IOError(error)
    with open(path, 'r') as settings_file:
        settings = json.load(settings_file)
    return settings

def save_json_file(options,path):
    if len(options) == 0:
        error = ('Options for path {0} must not be empty.')
        error = error.format(path)
        raise ValueError(error)
    if path == '':
        error = ('Path must not be empty.')
        raise ValueError(error)
    with open(path, 'w') as f:
        json.dump(options,
                  f,
                  encoding = 'utf-8',
                  indent = 4,
                  sort_keys = True)

def load_convert_options(path):
    options = load_json_file(path)
    return options

def parse_options(options):

    for key, val in options.items():
        if type(val) is str or unicode:
            if val.isdigit():
                options[key] = int(val)
            elif isfloat(val):
                options[key] = float(val)
            elif val.lower() == 'true':
                options[key] = True
            elif val.lower() == 'false':
                options[key] = False
    return options

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def load_default_convert_options(path):
    return load_json_file(path)