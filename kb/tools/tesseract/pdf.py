#!/usr/bin/python
import os
import subprocess
import shutil
from xml.etree import ElementTree as ET

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

def get_hocr_pdf(img_path,output_name):
    '''
    Creates a pdf-file by use of tesseract.
    '''
    cmd = 'tesseract {0} {1} -l dan pdf'
    cmd = cmd.format(img_path,output_name)
    run_cmd(cmd,shell=True)

def add_layers_to_pdf(temp,base_pdf,layers,output_path):
    '''
    Adds pdf-files on top of a base pdf-file by use of pdftk's stamp function.
    
    Input: 
        temp: to temp to process the layering.
        base_pdf: the pdf-file add the layers to.
        layers: a dictionary containing of extracted images. 'pdf_canvas' is a
            path to a pdf file to be added to the base pdf. Notice, pdf_canvas
            must have the same size (resolution) as base_pdf
        output_path: where to place the resulting pdf file.  
    '''
    if len(layers) == 0:
        shutil.move(base_pdf, output_path)
        return output_path
    index = 0
    temp_output_path = None
    for layer in layers.keys():
        temp_output_path = os.path.join(temp,str(index)+'.pdf')
        layer_pdf = layers[layer]['layer']
        add_layer_to_pdf(base_pdf,layer_pdf,temp_output_path)
        base_pdf = temp_output_path
        index += 1
    shutil.move(temp_output_path, output_path)

def add_layer_to_pdf(base_pdf,layer_pdf,output_path):
    cmd = 'pdftk {0} stamp {1} output {2}'
    cmd = cmd.format(base_pdf,layer_pdf,output_path)
    run_cmd(cmd,shell=True)

def merge_pdf_files(src,dest_path):
    pdfunite_src = os.path.join(src,'*')
    pdf_files = [f for f in os.listdir(src) if f.endswith('pdf')]
    if len(pdf_files) == 0:
        print 'No pdf files created!'
    elif len(pdf_files) == 1:
        shutil.move(os.path.join(src,pdf_files[0]),dest_path)
    else:
        cmd = 'pdfunite {0} {1}'
        cmd = cmd.format(pdfunite_src,dest_path)
        run_cmd(cmd,shell=True)
        clear_folder(src,True)

def create_canvas(images,page_x_size,page_y_size):
    '''
    For each image in a list of extracted images create a transparent pdf file 
    with the image at the same location as where it was originally extracted 
    from.
    '''
    
    for key in images.keys():
        # Create a pdf file from image file
        image_ext = os.path.basename(images[key]['file_path']).split('.')[-1]
        output_path = images[key]['file_path'].replace(image_ext,'pdf')
        input_path = images[key]['file_path']
        x_size = images[key]['width']
        y_size = images[key]['height']
        cmd = 'gs -sDEVICE=pdfwrite -o {0} -q -g{1}x{2} viewjpeg.ps -c \({3}\) viewJPEG'
        cmd = cmd.format(output_path,x_size,y_size,input_path)
        run_cmd(cmd,shell=True)
        # Place pdf file on a transparent pdf canvas with the specified size.
        input_path = output_path
        output_path = images[key]['file_path'].rstrip('.'+image_ext)+'_layer.pdf'
        x_nw = images[key]['x_nw']
        y_nw = images[key]['y_nw']
        y_sw = page_y_size - (y_size + y_nw)
        x_off = float(x_nw)/10
        y_off = float(y_sw)/10
        cmd ='gs -o {0} -sDEVICE=pdfwrite -g{1}x{2} -c "<</PageSize [{3} {4}] /PageOffset [{5} {6}]>> setpagedevice" -f {7}'
        cmd = cmd.format(output_path,page_x_size,page_y_size,
                         x_size,y_size,x_off,y_off,input_path)
        run_cmd(cmd,shell=True)
        images[key]['layer'] = output_path
    return images
        
def convert_to_bitonal(image_path,output_path,use_optimize2bw = False):
    '''
    Creates a bitonal tif-file with Group4 compression from an input image.
    Use either GraphicMagicks' convert or ExtactImage's optimize2bw.
    
    optimize2bw will generally give an image with thinner characters than
    GM's convert. Thus optimize2bw may be preferred to ink printed text.  
    
    '''    
    if use_optimize2bw:
        cmd = 'optimize2bw -i {0} -o {1}'
        cmd = cmd.format(image_path,output_path)
    else:
        convert_options = '-threshold 75% -monochrome -compress Group4'
        cmd = 'gm convert {0} {1} {2}'
        cmd = cmd.format(image_path, convert_options,output_path)
    run_cmd(cmd,shell=True)

def tiff_to_pdf(tiff_input_path,pdf_output_path):
    cmd = 'convert {0} {1}'
    cmd = cmd.format(tiff_input_path,pdf_output_path)
    run_cmd(cmd,shell=True)

def clear_folder(path,also_folder=False):
    '''
    Deletes all the files in a folder specified by "path". If specified by
    "also_folder", also delete the folder given by "path".
    '''
    if not os.path.isdir(path):
        error = '{0} is not a valid folder.'
        error = error.format(path)
        raise IOError(error)
    for f in os.listdir(path):
        f_path = os.path.join(path,f)
        os.remove(f_path)
    if also_folder:
        os.rmdir(path)

def create_tesseract_file(image_path,hocr_path,overwrite_existing=False):
    '''
    Creates a hocr file from the given image file in "image_path" and return
    the path for the resulting hocr file.
    If a hocr file already exist, don't create a new one. 
    '''
    if hocr_path.endswith('.hocr'):
        ret_path = hocr_path
    else:
        ret_path = hocr_path+'.hocr'
    if os.path.exists(ret_path) and not overwrite_existing:
        return ret_path
    cmd = 'tesseract {0} {1} -l dan hocr'
    cmd = cmd.format(image_path,hocr_path)
    run_cmd(cmd,shell=True)
    return ret_path

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
        run_cmd(cmd,True)
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
    run_cmd(crop_cmd,True)
    return  illustrations

def get_image_size(xml_file,image_path):
    '''
    Todo: document this
    '''
    failed = False
    try:
        tree,ns = parse_and_get_ns(xml_file)
        ns = ns['']
        xpath = ".//{0}div[@class='ocr_page']".format(ns)
        page_info = tree.find(xpath)
        image_bbox = page_info.attrib['title'].split(';')
        size = [c for c in image_bbox[1].split() if c.isdigit() and int(c) > 0]
    except:
        failed = True
    width, height= int(size[0]),int(size[1])
    failed = (failed or width == 0 or height == 0)
    if failed:
        try:
            # Use identify instead
            cmd = 'indentify {0}'.format(image_path)
            identify_info = subprocess.check_output(cmd,shell=True)
            size = identify_info.split[2].split('x')
        except:
            return None, None
    width, height= int(size[0]),int(size[1])
    return width, height

def get_illustrations_bboxes(xml_file):
    try:
        tree,ns = parse_and_get_ns(xml_file)
        ns = ns['']
        bboxes = set()
        # Locate illustrations marked with empty span-element
        elems = tree.findall('.//*[@class="ocr_line"]')
        for elem in elems:
            illustration_elem =  find_illustration_level(tree,elem)
            # Check if title is in parent before check its children
            if (illustration_elem is None or
                (illustration_elem is not None and
                 'title' not in illustration_elem.attrib)
                ):
                continue
            bbox = illustration_elem.attrib['title'].split(';')[0]
            bboxes.add(bbox)
        return list(bboxes)
    except:
        return None

def find_illustration_level(tree,elem):
    if 'id' not in elem.attrib:
        return None
    if has_only_illustrations(elem):
        elem_id = elem.attrib['id']
        parent_elem = tree.find('.//*[@id="{0}"]/..'.format(elem_id))
        valid_parent = find_illustration_level(tree,parent_elem)
        if valid_parent is None:
            return elem
        return valid_parent
    else:
        return None
        
def has_only_illustrations(elem):
    if len(elem.findall("./*")) == 0:
        return is_illustration(elem)
    else:
        sub_elems = elem.findall("./*")
        for elem in sub_elems:
            if not has_only_illustrations(elem): return False 
    return True

def is_illustration(elem):
    if elem.text is None:
        return True
    if elem.text.strip() == '':
        return True
    return False
    
def parse_and_get_ns(file_path):
    events = "start", "start-ns"
    root = None
    ns = {}
    for event, elem in ET.iterparse(file_path, events):
        if event == "start-ns":
            if elem[0] in ns and ns[elem[0]] != elem[1]:
                raise KeyError("Duplicate prefix with different URI found.")
                # NOTE: It is perfectly valid to have the same prefix refer
                #     to different URI namespaces in different parts of the
                #     document. This exception serves as a reminder that this
                #     solution is not robust.    Use at your own peril.
            ns[elem[0]] = "{%s}" % elem[1]
        elif event == "start":
            if root is None:
                root = elem
    return ET.ElementTree(root), ns

def delta_time(t):
    t = int(t * 100) / 100.0
    h, remainder = divmod(t, 3600)
    remainder = round(remainder,3)
    m, remainder = divmod(remainder, 60)
    s, ms = divmod(remainder, 1)
    ms = round(ms,2)*100
    ret_str = ''
    if h > 0:
        ret_str += str(int(h))+' h, '
    if m > 0:
        ret_str += str(int(m))+' m, '
    if s > 0 or ms > 0:
        if ms > 0:
            ret_str += (str(int(s))+'.'+str(int(ms))+' s')
        else:
            ret_str += str(int(s))+' s'
    return ret_str.rstrip(', ')

def run_cmd(cmd,shell=False,print_output=False):
    '''
    
    '''
    try:
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=shell)
    except Exception as e:
        raise e
    error_code = process.poll()
    output = process.communicate()[0]
    if error_code > 0:
        err = 'Process failed with error code {0}. Process output was: {1}.'
        err = err.format(error_code,output)
        raise IOError(err)
    if print_output:
        print output
    return output