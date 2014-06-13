'''
Created on 06/06/2014

@author: jeel
'''

import os
import time
import subprocess


def create_temp_pdf_files(convert_options,
                          temp_folder,
                          max_batch_size = 10,
                          log_count = 20,
                          logger = None):
    '''
    Convert images in batches group after their convert_options and
    output the separate pdf-files to temp_folder
    
    '''
    batch = []
    created_pdfs = 0
    images_converted = 0
    total_conv_time = 0
    images = list(convert_options.keys())
    images.sort()
    temp_pdf_files = []
    try:
        images_empty = len(images) == 0
        batch_empty = len(batch) == 0
        while (not images_empty or (images_empty and not batch_empty)):
            
            if not images_empty:
                image = images.pop(0)
                if len(batch) == 0:
                    # Add image to new batch
                    batch.append(convert_options[image])
                    continue
                same_settings = (batch[0]['convert_options'] == \
                             convert_options[image]['convert_options'])
                full_batch = len(batch) >= max_batch_size
                if same_settings and not full_batch:
                    batch.append(convert_options[image])
                    continue
                next_batch = [convert_options[image]]
            created_pdfs += 1
            start_time = time.time()
            output_name = 'output' + str(created_pdfs).zfill(4) + '.pdf'
            temp_path = os.path.join(temp_folder,output_name)
            convert_to_pdf(batch,temp_path)
            conversion_time = time.time() - start_time
            total_conv_time += conversion_time
            temp_pdf_files.append(temp_path)
            if logger:
                images_converted += len(batch)
                avg_conversion_time = total_conv_time / images_converted
                remaining_images = len(convert_options) - images_converted
                remaining_time = avg_conversion_time * remaining_images
                first_batch = images_converted == len(batch)
                last_file = remaining_images == 0
                log_step = ((images_converted - len(batch)) % log_count) > \
                            (images_converted % log_count)
                if  first_batch or last_file or log_step:
                    msg = ('{0} of {1} images has been converted.')
                    msg = msg.format(str(images_converted),
                                     str(len(convert_options)))
                    logger.debug(msg)
                    msg = ('Files remaining: {0}.')
                    msg = msg.format(str(remaining_images))
                    logger.debug(msg)
                    msg = ('Avg. conversion time: {0} per image')
                    msg = msg.format(str(delta_time(avg_conversion_time)))
                    logger.debug(msg)
                    msg = ('Estimated time left: {0}.')
                    msg = msg.format(str(delta_time(remaining_time)))
                    logger.debug(msg)
            batch = next_batch
            next_batch = []
            images_empty = len(images) == 0
            batch_empty = len(batch) == 0
    except Exception as e:
        clear_pdf_conversion(temp_folder)
        raise e
    if logger:
        msg = ('Conversion to temp files took {0}')
        msg = msg.format(delta_time(total_conv_time))
        logger.debug(msg)
    return temp_pdf_files


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

def convert_to_pdf(file_list,output_file_path):
    '''
    Use ImageMagicks "convert" to convert a list of files as defined in a 
    dictionary with convert options and file paths.
    '''
    file_paths = []
    for file_info in file_list:
        file_path = file_info['path']
        file_paths.append(file_path)
        if not os.path.isfile(file_path):
            error = ('The file {0} does not exist or path is wrong.')
            error = error.format(file_path)
            raise NameError()
    # All files to be converted are a batch with some convert options
    files_str = " ".join(file_paths)
    output_settings = file_list[0]['convert_options']
    cmd = ('convert {0} {1} "{2}"')
    cmd = cmd.format(files_str,output_settings,output_file_path)
    output = subprocess.check_output(cmd, shell = True)
    if output != "":
        error = ('Output from convert: {0}')
        error = error.format(output)
        raise ValueError(error)
    
def merge_temp_pdf_files(temp_folder,temp_pdf_files,output_pdf_path):
    '''
    Merge all the temporary pdf files in temp_folder. The merging
    is done ten files at the time to avoid overloading the merge program.
    '''
    pdfs1 = temp_pdf_files
    pdfs2 = []
    merge_count = 0
    try:
        while len(pdfs1) > 1 or len(pdfs2) > 1:
            if len(pdfs1) > 1:
                (pdfs1, pdfs2, merge_count) = merge_pdf_files(pdfs1,
                                                              pdfs2,
                                                              temp_folder,
                                                              merge_count)
            if len(pdfs2) > 1:
                (pdfs2, pdfs1, merge_count) = merge_pdf_files(pdfs2,
                                                              pdfs1,
                                                              temp_folder,
                                                              merge_count)
        if len(pdfs1) == 1:
            os.rename(pdfs1[0], output_pdf_path)
        elif len(pdfs2) == 1:
            os.rename(pdfs2[0], output_pdf_path)
    except Exception as e:
        clear_pdf_conversion(temp_folder)
        raise e

def merge_pdf_files(input_pdfs, output_pdfs, folder, count):
    '''
    Merge ten files at the time.
    TODO: Add merge amount to config
    '''
    while len(input_pdfs) > 0:
        merge_file_paths = []
        if len(input_pdfs) > 12:
            merge_file_paths = input_pdfs[:10]
            input_pdfs = input_pdfs[10:]
        else:
            merge_file_paths = input_pdfs
            input_pdfs = []
        count += 1
        output_file_name = 'merge_output_' + str(count).zfill(4) + \
            '.pdf'
        output_file_path = os.path.join(folder,output_file_name)
        merge_cmd = 'pdfunite "' + '" "'.join(merge_file_paths) + '" "' + \
            output_file_path + '"'
        subprocess.check_output(merge_cmd, shell = True)
        output_pdfs.append(output_file_path)
    return (input_pdfs, output_pdfs, count)

def clear_pdf_conversion(path,also_folder=False):
    for f in os.listdir(path):
        f_path = os.path.join(path,f)
        os.rmdir(f_path)