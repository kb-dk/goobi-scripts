'''
Created on 14/06/2014

@author: jeel
'''
import os
import time
from tools.tesseract import pdf, hocr2pdf
import sys
import shutil
import logging
import logging.handlers

def setup_logger(log_path,logger_name=None,log_format=None):
    if not log_format:
        log_format = ('%(levelname) -6s %(asctime)s %(name)' 
                      ' -10s %(funcName) -10s %(lineno)'
                      '-5d: %(message)s')
    if log_path.endswith(os.sep) and not os.path.exists(log_path):
        err_msg = 'No such directory: '+log_path
        raise IOError(err_msg)
    elif not os.path.exists(log_path[:log_path.rfind(os.sep)]):
        err_msg = 'No such directory: '+\
            log_path[:log_path.rfind(os.sep)]
        raise IOError(err_msg)
    if not logger_name:
        logger_name = 'Tesseract Logger'
    logger = logging.getLogger(logger_name)
    
    fmt = logging.Formatter(log_format)
    rotating_handler = logging.handlers.RotatingFileHandler(
                        log_path,maxBytes=(1024*1024),backupCount=10,
                        )
    rotating_handler.setFormatter(fmt)
    logger.addHandler(rotating_handler)
    logging.basicConfig(level = logging.DEBUG,
                        format = log_format)
    msg = 'Logger initiated...'
    logger.debug(msg)
    return logger

def create_ebook(src,temp,dest_path):
    
    # Load variables
    valid_exts = ['tif', 'tiff', 'jpg', 'jpeg', 'jpe', 'jif', 'jfif',
                  'jfi', 'jp2', 'j2k', 'jpf', 'jpx', 'jpm', 'mj2']
    if not os.path.isdir(os.path.dirname(temp.rstrip(os.sep))):
        err = '{0} is not a valid folder.'.format(temp)
        raise IOError(err)
    images = [os.path.join(src,i) for i in sorted(os.listdir(src))
              if i.split('.')[-1] in valid_exts]
    img_tmp = os.path.join(temp,'img_tmp')
    pdf_tmp = os.path.join(temp,'pdf_tmp')
    dest_dir = os.path.dirname(dest_path)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    index = 1
    logger = setup_logger(os.path.join(dest_dir,'log.txt'))
    if len(images) == 0:
        msg = 'No images found in {0}.'
        msg = msg.format(src)
        logger.debug(msg)
        return
    script_start = time.time()
    for image_path in images:
        create_pdf_start = time.time()
        create_image(image_path,img_tmp,pdf_tmp,600,index,logger)
        msg = 'Page {0} ({1}) created in {2}'
        msg = msg.format(index,image_path,
                         pdf.delta_time(time.time()-create_pdf_start))
        if logger: logger.debug(msg)
        index += 1
    pdf.merge_pdf_files(pdf_tmp,dest_path)
    msg = ('Total time: {0}')
    msg = msg.format(pdf.delta_time(time.time()-script_start))
    if logger: logger.debug(msg)

def create_image(image_path,img_tmp,pdf_tmp,dpi,page_nr,logger=None):
    # Load variables
    use_bw_for_tesseract = False
    use_optimize2bw = False
    image_file_name = os.path.basename(image_path).split('.')[0]
    finished_path = os.path.join(pdf_tmp,image_file_name+'.pdf')
    if os.path.exists(finished_path) and os.path.isfile(finished_path):
        return
    illustration_size_limit_pct = 0.01
    
    text_background_quality = 90
    extract_quality = 50
    extract_resize = 25
    hori_ratio = 0.002
    vert_ratio = 150

    pdf.find_or_create_dir(img_tmp,pdf_tmp)
    hocr_file_name = os.path.join(img_tmp,image_file_name)
    if use_bw_for_tesseract:
        tesseract_input = os.path.join(img_tmp,'tesseract_input.tif')
        pdf.convert_to_bitonal(image_path,
                               tesseract_input, 
                               use_optimize2bw=use_optimize2bw)
    else:
        tesseract_input = image_path
    hocr_file_path = pdf.create_tesseract_file(tesseract_input,hocr_file_name)
    page_width,page_height = pdf.get_image_size(hocr_file_path,image_path)
    if page_width is None:
        err = 'Size of image ({0}) cannot be detected for page {1}.'
        err = err.format(image_path,page_nr)
        raise IOError(err)
    illustration_size_limit = (((page_width+page_height)/2)
                               *illustration_size_limit_pct)
    coordinates = pdf.get_illustrations_bboxes(hocr_file_path)
    if (coordinates is None or 
        (coordinates is not None and len(coordinates) == 0)):
        #logger.debug 'No illustrations detected.'
        use_illustrations = False
    else:
        use_illustrations = True
    if use_illustrations:
        text_background_jpeg = os.path.join(img_tmp,'text.jpg')
        illustrations = pdf.extract_illustrations(image_path,
                                                  coordinates,
                                                  img_tmp,
                                                  text_background_jpeg,
                                                  illustration_size_limit = illustration_size_limit,
                                                  text_background_quality = text_background_quality,
                                                  extract_quality = extract_quality,
                                                  extract_resize = extract_resize,
                                                  hori_ratio = hori_ratio,
                                                  vert_ratio = vert_ratio,
                                                  logger = logger
                                                  )
        msg = '{0} of {1} illustrations used in page {2}.'
        msg = msg.format(len(illustrations),len(coordinates),page_nr)
        if logger: logger.debug(msg)
    else:
        text_background_jpeg = image_path
    background_tif =  os.path.join(img_tmp,'background.tif')
    pdf.convert_to_bitonal(text_background_jpeg,
                           background_tif, 
                           use_optimize2bw=use_optimize2bw)
    background_pdf = os.path.join(img_tmp,'background.pdf')
    pdf.tiff_to_pdf(background_tif, background_pdf)
    hocr_background_pdf = os.path.join(img_tmp,'hocr_background.pdf')
    try:
        hocr_pdf = os.path.join(img_tmp,'hocr.pdf')
        hocr2pdf.make_text_layer(hocr_path = hocr_file_path,
                                 output_pdf_path = hocr_pdf,
                                 image_width = page_width,
                                 image_hight = page_height,
                                 image_dpi = dpi)
        pdf.add_layer_to_pdf(hocr_pdf,background_pdf,hocr_background_pdf)
    except Exception as e:
        msg = 'An error occured when using hocr-pdf:'+str(e)
        if logger: logger.debug(msg)
        pdf.get_hocr_pdf(background_tif,hocr_background_pdf)
    if use_illustrations:
        try:
            layers = pdf.create_canvas(illustrations,page_width,page_height)
            pdf.add_layers_to_pdf(img_tmp,hocr_background_pdf,
                                  layers,finished_path)
        except Exception as e:
            msg = ('An exception occured for file {0} when adding layers to '
                   'background: {1}. Creating bitonal tif-pdf without ocr '
                   'as a substitute.')
            msg = msg.format(image_path,str(e))
            if logger: logger.debug(msg)
            alternative_tif = os.path.join(img_tmp,'alternative.tif')
            pdf.convert_to_bitonal(image_path,
                                   alternative_tif, 
                                   use_optimize2bw=use_optimize2bw)
            pdf.tiff_to_pdf(alternative_tif, finished_path)
    else:
        shutil.move(hocr_background_pdf,finished_path)
    pdf.clear_folder(img_tmp)

if __name__ == '__main__':
    if not len(sys.argv) == 4:
        print("Usage: %s <source> <temp work folder> <destination>\n" 
              % os.path.basename(sys.argv[0]))
    else:
        create_ebook(sys.argv[1],sys.argv[2],sys.argv[3])