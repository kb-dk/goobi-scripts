#!/usr/bin/python
import os
import shutil

from tools.processing import processing
from tools.filesystem import fs

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
    for layer in layers:
        temp_output_path = os.path.join(temp,str(index)+'.pdf')
        layer_pdf = layer['layer']
        add_layer_to_pdf(base_pdf,layer_pdf,temp_output_path)
        base_pdf = temp_output_path
        index += 1
    shutil.move(temp_output_path, output_path)

def add_layer_to_pdf(base_pdf,layer_pdf,output_path):
    cmd = 'pdftk {0} stamp {1} output {2}'
    cmd = cmd.format(base_pdf,layer_pdf,output_path)
    processing.run_cmd(cmd,shell=True)

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
        processing.run_cmd(cmd,shell=True)
        fs.clear_folder(src,True)

def create_canvas(images,page_x_size,page_y_size):
    '''
    For each image in a list of extracted images create a transparent pdf file 
    with the image at the same location as where it was originally extracted 
    from.
    '''
    
    for image in images:
        # Create a pdf file from image file
        image_ext = os.path.basename(image['file_path']).split('.')[-1]
        output_path = image['file_path'].replace(image_ext,'pdf')
        input_path = image['file_path']
        x_size = image['width']
        y_size = image['height']
        cmd = 'gs -sDEVICE=pdfwrite -o {0} -q -g{1}x{2} viewjpeg.ps -c \({3}\) viewJPEG'
        cmd = cmd.format(output_path,x_size,y_size,input_path)
        processing.run_cmd(cmd,shell=True)
        # Place pdf file on a transparent pdf canvas with the specified size.
        input_path = output_path
        output_path = image['file_path'].rstrip('.'+image_ext)+'_layer.pdf'
        x_nw = image['x_nw']
        y_nw = image['y_nw']
        y_sw = page_y_size - (y_size + y_nw)
        x_off = float(x_nw)/10
        y_off = float(y_sw)/10
        cmd ='gs -o {0} -sDEVICE=pdfwrite -g{1}x{2} -c "<</PageSize [{3} {4}] /PageOffset [{5} {6}]>> setpagedevice" -f {7}'
        cmd = cmd.format(output_path,page_x_size,page_y_size,
                         x_size,y_size,x_off,y_off,input_path)
        processing.run_cmd(cmd,shell=True)
        image['layer'] = output_path
    return images
        
def tiff_to_pdf(tiff_input_path,pdf_output_path):
    cmd = 'convert {0} -monochrome -compress Group4 {1}'
    cmd = cmd.format(tiff_input_path,pdf_output_path)
    processing.run_cmd(cmd,shell=True)

def image_to_bw_pdf(input_path,pdf_output_path,threshold):
    cmd = 'convert {0} -threshold {1} -monochrome -compress Group4 {2}'
    cmd = cmd.format(input_path,threshold,pdf_output_path)
    processing.run_cmd(cmd,shell=True)

def image_to_color_pdf(image_input,pdf_output_path,input_dpi,quality,resize):
    # This will give the new density of the resized image, so it fits with the
    # other images, e.g. resize: 25 (%) => 600/(25/100.0) = 150 DPI
    density = input_dpi*(resize/100.0)
    cmd = 'convert {0} -quality {1}% -resize {2}% -density {3} {4}'
    cmd = cmd.format(image_input,quality,resize,density,pdf_output_path)
    processing.run_cmd(cmd,shell=True)
