'''
Created on 19/08/2014

@author: jeel
'''
import os
def getImages(src):
    img_dict = dict()
    images = [os.path.join(src,f) for f in os.listdir(src)]
    for image in images:
        img = dict()
        e = image.rsplit('.',1)[-1].lower()
        mimetype = None
        if e in ['tif','tiff']:
            mimetype = 'image/tiff'
        elif e in ['jpeg','jpg']:
            mimetype = 'image/jpeg'
        if mimetype is None:
            continue
        img['mimetype'] = mimetype
        img_dict[image] = img
    return img_dict