#coding:utf-8
import json
import os
from PIL import Image
import numpy as np
import pydicom

def doencode(a):
    out = dict()
    for key, value in a.items():
        akey = key
        if isinstance(value, int):
            avalue = str(value)
        else:
            avalue = value
        out[akey] = avalue
    return out

def decodeImage(fname):
    try:
        img = Image.open(fname)
        im = np.asarray(img)
        # if im.shape[0] == 1080 and im.shape[1] == 1920:
        #     im = im[5:942, 596:1675, :].copy()
        im = autoCutImage(im, 50)
        return 'jpg', Image.fromarray(im)
    except IOError:
        img = pydicom.read_file(fname)
        img = img.PixelData
        img = img[20:]
        tmp = open('tmp.jpg', 'wb')
        tmp.write(img)
        tmp.close()
        img = Image.open('tmp.jpg')
        img = np.asarray(img)
        # if img.shape[0] == 1020 and img.shape[1] == 1276:
        #     img = img[:911, 87:1166, :].copy()
        #     return Image.fromarray(img)
        return 'dicom', Image.fromarray(img)


def autoCutImage(img, thresh):
    image = np.asarray(img, dtype=np.int64)
    # img = image.reshape((img.shape[0], img.shape[1]*img.shape[2]))
    # out = np.zeros(img.shape[0], dtype=int64)
    img = np.add.reduce(image, 2)
    img = img > thresh
    img = np.add.reduce(img, 1)
    themin = np.int64(0)
    imin = 0
    themax = np.int64(0)
    imax = 0
    tmp = np.int64(0)
    for i in range(img.shape[0]-1):
        tmp = img[i+1] - img[i]
        if tmp < themin:
            themin = tmp
            imin = i
    image = image[:imin, :, :].copy()
    themin = np.int64(0)
    imin = 0
    themax = np.int64(0)
    imax = 0
    tmp = np.int64(0)
    img = np.add.reduce(image, 2)
    img = img > thresh
    img = np.add.reduce(img, 0)
    for i in range(img.shape[0]-1):
        tmp = img[i+1] - img[i]
        if tmp < themin:
            themin = tmp
            imin = i
            continue
        if tmp > themax:
            themax = tmp
            imax = i
    if imin-imax < 800:
        image = image[:, 595:1675, :]
    else:
        image = image[:, imax:imin, :].copy()
    image = np.asarray(image, dtype=np.uint8)
    return image


def readjson(dirname):
    # dirname = unicode(dirname)
    files = os.listdir(dirname)
    os.chdir(dirname)
    os.mkdir('output')
    out = []
    for filename in files:
        if os.path.splitext(filename)[1] == '.json':
            os.chdir(dirname)
            f = open(filename, 'rb')
            f = json.load(f)
            patientinf = f['patient_info']
            # patientinf = doencode(patientinf)
            endoscopyinfo = f['endoscopy_info']
            endoscopyinfo = doencode(endoscopyinfo)
            pathologyinfo = f['pathology_info']
            fname = f['file_path'].replace('\\', '/')
            os.chdir('..')
            assert os.path.exists(fname)
            finalname = os.path.basename(fname) + '.jpg'
            try:
                filetype, im = decodeImage(fname)
            except Exception as e:
                print(e)
                print('Error happened in File: ' + fname)
                continue
            if im is not None:
                os.chdir(dirname + '/output')
                im.save(finalname)
                image = {
                    'annotations': [],
                    'class': 'image',
										'filetype': filetype,
                    'filename': finalname,
                    'md5': '',
                    'time': [],
                    'patientinf': patientinf,
                    'endoscopyinfo': endoscopyinfo,
                    'pathologyinfo': pathologyinfo
                }
                out.append(image)
    os.chdir(dirname + '/output')
    f = open('out.json', 'w')
    json.dump(out, f, indent=4, separators=(',', ': '), sort_keys=True)
    f.write('\n')
    f.close()
