#!/usr/bin/python
import os
import subprocess
import sys
import time
import shlex
from xml.etree import ElementTree as ET

def create_image(image_paths):
    if type(image_paths) is str:
        image_paths = [image_paths]
    print image_paths
    for image_path in image_paths:
        print 'Converting {0} to pdf'.format(image_path)
        ext = os.path.basename(image_path).split('.')[-1]
        script_start = time.time()
        output_folder = 'temp'
        finished_pdfs = 'finished'
        image_file_name = os.path.basename(image_path)
        find_or_create_dir(output_folder,finished_pdfs)
        finished_path = os.path.join(finished_pdfs,
                                     image_file_name.replace(ext,'pdf'))
        clear_folder(output_folder)
        start = time.time()
        hocr_file_path = os.path.join(output_folder,image_file_name.replace('.'+ext,''))
        hocr_file = create_tesseract_file(image_path,hocr_file_path)
        #print 'Create hOCR-file: '+delta_time(time.time()-start)
        start = time.time()
        x_size,y_size = get_image_size(hocr_file)
        #print 'Get image size: '+delta_time(time.time()-start)
        start = time.time()
        ill_coord_list = get_illustrations_bboxes(hocr_file)
        if not ill_coord_list is None and len(ill_coord_list) > 0:
            if len(ill_coord_list) == 1:
                print '\tOne illustration detected.'
            else:
                print '\t{0} illustrations detected.'.format(len(ill_coord_list))
            #print 'Get coordinates for illustrations: '+delta_time(time.time()-start)
            start = time.time()
            background, ill_list = extract_illustrations(image_path,
                                                         ill_coord_list,
                                                         output_folder)
        else:
            
            background = image_path
            #print 'Extract illustrations from image: '+delta_time(time.time()-start)
        start = time.time()
        output_base_name =  os.path.join(output_folder,image_file_name.replace('.'+ext,''))
        background = convert_to_bitonal(background,
                                        output_base_name, 
                                        use_optimize2bw=False)
        #print 'Convert background to bitonal: '+delta_time(time.time()-start)
        start = time.time()
        if not ill_coord_list is None and len(ill_coord_list) > 0:
            ill_list = create_canvas(ill_list,x_size,y_size)
            #print 'Create canvases with illustrations: '+delta_time(time.time()-start)
            start = time.time()
        hocr_pdf = get_hocr_pdf(background)
        #print 'Create text hOCR-pdf: '+delta_time(time.time()-start)
        start = time.time()
        if not ill_coord_list is None and len(ill_coord_list) > 0:
            final_pdf = stamp_pdf(output_folder,hocr_pdf,ill_list,finished_path)
            #print 'Add illustrations to text hOCR-pdf: '+delta_time(time.time()-start)
        else:
            os.rename(hocr_pdf,finished_path)
        print '\tTotal time: '+ delta_time(time.time()-script_start)
        clear_folder(output_folder)

def find_or_create_dir(*paths):
    '''
    Given a folder path, check to see 
    if folder exists or create it
    Raises exception in case of error
    '''
    for path in paths:
        if os.path.exists(path):
            if not os.path.isdir(path):
                error = '{0} exists but is not a valid directory.'.format(path)
                raise IOError(error)
        elif not os.path.exists(path):
            os.makedirs(path)

def get_hocr_pdf(input_path,output_path=None):
    if not output_path:
        output_path = input_path.replace('.tif','')
    cmd = 'tesseract {0} {1} -l dan pdf'
    cmd = cmd.format(input_path,output_path)
    run_cmd(cmd)
    return output_path+'.pdf'

def stamp_pdf(folder,input_path,stamps,output_path):
    index = 0
    temp_output_path = None
    for stamp in stamps.keys():
        temp_output_path = os.path.join(folder,str(index)+'.pdf')
        canvas_stamp = stamps[stamp]['pdf_canvas']
        cmd = 'pdftk {0} stamp {1} output {2}'
        cmd = cmd.format(input_path,canvas_stamp,temp_output_path)
        run_cmd(cmd)
        input_path = temp_output_path
        index += 1
    if not temp_output_path is None:
        os.rename(temp_output_path, output_path)
    return output_path

def create_canvas(ill_list,page_x_size,page_y_size):
    for ill in ill_list.keys():
        ext = os.path.basename(ill_list[ill]['file_path']).split('.')[-1]
        output_path = ill_list[ill]['file_path'].replace(ext,'pdf')
        input_path = ill_list[ill]['file_path']
        x_size = ill_list[ill]['x_size']
        y_size = ill_list[ill]['y_size']
        cmd = 'gs -sDEVICE=pdfwrite -o {0} -q -g{1}x{2} viewjpeg.ps -c \({3}\) viewJPEG'
        cmd = cmd.format(output_path,x_size,y_size,input_path)
        run_cmd(cmd)
        ill_list[ill]['pdf'] = output_path
    for ill in ill_list.keys():
        ext = os.path.basename(ill_list[ill]['file_path']).split('.')[-1]
        output_path = ill_list[ill]['file_path'].rstrip('.'+ext)+'_canvas.pdf'
        input_path = ill_list[ill]['pdf']
        x_size = ill_list[ill]['x_size']
        y_size = ill_list[ill]['y_size']
        x_nw = ill_list[ill]['x_nw']
        y_nw = ill_list[ill]['y_nw']
        y_sw = page_y_size - (y_size + y_nw)
        x_off = float(x_nw)/10
        y_off = float(y_sw)/10
        cmd ='gs -o {0} -sDEVICE=pdfwrite -g{1}x{2} -c "<</PageSize [{3} {4}] /PageOffset [{5} {6}]>> setpagedevice" -f {7}'
        cmd = cmd.format(output_path,page_x_size,page_y_size,x_size,y_size,x_off,y_off,input_path)
        run_cmd(cmd)
        ill_list[ill]['pdf_canvas'] = output_path
    return ill_list
        
def convert_to_bitonal(input_path,output_path,use_optimize2bw = False):
    output_path = output_path+'.tif'
    if use_optimize2bw:
        cmd = 'optimize2bw -i {0} -o {1}'
        cmd = cmd.format(input_path,output_path)
    else:
        convert_options = '-threshold 75% -monochrome -compress Group4'
        cmd = 'gm convert {0} {1} {2}'
        cmd = cmd.format(input_path, convert_options,output_path)
    run_cmd(cmd)
    return output_path

def clear_folder(path,also_folder=False):
    for f in os.listdir(path):
        f_path = os.path.join(path,f)
        os.remove(f_path)
    if also_folder:
        os.rmdir(path)

def create_tesseract_file(image_path,output_file_path):
    ret_path = output_file_path+'.hocr'
    if os.path.exists(ret_path):
        return ret_path
    cmd = 'tesseract {0} {1} -l dan hocr'
    cmd = cmd.format(image_path,output_file_path)
    run_cmd(cmd,shell=False)
    return ret_path

def extract_illustrations(image_name, ill_coord_list,output_folder):
    ext = os.path.basename(image_name).split('.')[-1]
    crop_cmd = 'gm convert '+image_name+' '
    illustrations = {}
    ill_index = 0
    for coord_list in ill_coord_list:
        coord_list = [c for c in coord_list.split() if c.isdigit()]
        if not len(coord_list) == 4:
            print('Bbox coordinates "{0}"not valid '.format(coord_list))
            print('Bbox coordinate list must contain four digits, e.g "bbox 612 301 2433 418"')
            return
        # nw = north west, se = south east
        x_nw = int(coord_list[0])
        y_nw = int(coord_list[1])
        x_se = int(coord_list[2])
        y_se = int(coord_list[3])
        x_size = x_se-x_nw
        y_size = y_se-y_nw
        
        ratio = float(x_size)/float(y_size)
        if ratio < 0.01 or ratio > 25:
            continue
        output_file_name = str(ill_index)+'_{0}x{1}+{2}+{3}.jpg'
        output_file_name = output_file_name.format(x_size,y_size,x_nw,y_nw)
        output_file_path = os.path.join(output_folder,output_file_name)
        output_settings = '-crop {0}x{1}+{2}+{3} -quality 50% -resize 25%'
        output_settings = output_settings.format(x_size,y_size,x_nw,y_nw)
        cmd = ('gm convert {0} {1} "{2}"')
        cmd = cmd.format(image_name,output_settings,output_file_path)
        print cmd
        run_cmd(cmd,True)
        illustrations[ill_index] = {'x_nw': x_nw,
                                    'y_nw': y_nw,
                                    'x_se': x_se,
                                    'y_se': y_se,
                                    'x_size': x_size,
                                    'y_size': y_size,
                                    'file_path': output_file_path,
                                    }
        # add options to remove region convert command 
        output_settings = ' -region {0}x{1}+{2}+{3} -fill white -colorize 100%'
        output_settings = output_settings.format(x_size,y_size,x_nw,y_nw)
        crop_cmd += output_settings
        ill_index += 1
    output_file_name = 'text.jpg'
    text_background = os.path.join(output_folder,output_file_name)
    crop_cmd += ' -quality 90% '+text_background 
    run_cmd(crop_cmd,True)
    return text_background, illustrations

def get_image_size(xml_file):
    tree,ns = parse_and_get_ns(xml_file)
    ns = ns['']
    xpath = ".//{0}div[@class='ocr_page']".format(ns)
    page_info = tree.find(xpath)
    image_bbox = page_info.attrib['title'].split(';')
    size = [c for c in image_bbox[1].split() if c.isdigit() and int(c) > 0]
    return int(size[0]),int(size[1]) 

def get_illustrations_bboxes(xml_file):
    tree,ns = parse_and_get_ns(xml_file)
    ns = ns['']
    ill_list = []
    
    # Locate illustrations marked with empty span-element
    xpath = ".//{0}span[@class='ocrx_word']".format(ns)
    ocr_spans = tree.findall(xpath)
    illustrations = ([span for span in ocr_spans 
                     if (len(span.findall("./*")) == 0 and 
                         span.text == ' ')
                    ])
    ill_list += [i.attrib['title'].split(';')[0] for i in illustrations]
    # Locate illustrations marked with empty em-element
    xpath = ".//{0}em/..".format(ns)
    ocr_spans = tree.findall(xpath)
    illustrations = ([span for span in ocr_spans 
                     if (span.find("./{0}em".format(ns)).text == ' ')
                     ])
    ill_list += [i.attrib['title'].split(';')[0] for i in illustrations]
    return ill_list        
    
def parse_and_get_ns(file_path):
    events = "start", "start-ns"
    root = None
    ns = {}
    for event, elem in ET.iterparse(file_path, events):
        if event == "start-ns":
            if elem[0] in ns and ns[elem[0]] != elem[1]:
                # NOTE: It is perfectly valid to have the same prefix refer
                #     to different URI namespaces in different parts of the
                #     document. This exception serves as a reminder that this
                #     solution is not robust.    Use at your own peril.
                raise KeyError("Duplicate prefix with different URI found.")
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
    if s > 0:
        ret_str += str(int(s))+' s, '
    if ms > 0:
        ret_str += str(int(ms))+' ms'
    return ret_str.rstrip(', ')


def run_cmd(cmd,shell=False):
    FNULL = open(os.devnull,'w')
    try:
        if shell:
            output = subprocess.check_call(cmd,
                                           stdout=FNULL,
                                           stderr=subprocess.STDOUT,
                                           shell=shell)
        else:
            output = subprocess.check_call(shlex.split(cmd),
                                           stdout=FNULL,
                                           stderr=subprocess.STDOUT,
                                           shell=shell)
    except Exception as e:
        FNULL.close()
        raise e
    FNULL.close()
    if output:
        raise IOError('{0} failed'.format(cmd))

if __name__ == "__main__":
    valid_exts = ['tif', 'tiff', 'jpg', 'jpeg', 'jpe', 'jif', 'jfif',
                   'jfi', 'jp2', 'j2k', 'jpf', 'jpx', 'jpm', 'mj2']
    if len(sys.argv) == 1:
        print("Usage: %s <image_file_path>\n" % os.path.basename(sys.argv[0]))
    else:
        if os.path.isdir(sys.argv[1]):
            folder = sys.argv[1]
            create_image([os.path.join(folder,f) for f in os.listdir(folder)
                          if f.split('.')[-1] in valid_exts])
        else:
            create_image(sys.argv[1])