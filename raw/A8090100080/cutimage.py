from PIL import Image
import numpy as np
import os


def loadImage(filename):

    if not os.path.exists(filename):
        print('filename does not exist!')
        return None
    im = Image.open(filename)
    im = np.asarray(im)
    return im

def cutImage(im):
    out = np.zeros((im.shape[1], im.shape[2]), dtype=np.int64)
    for i in range(im.shape[1]):
        for j in range(im.shape[0]):
            for k in range(im.shape[2]):
                out[i, k] += im[j, i, k]
    for i in range(im.shape[1]):
        print(out[i, :])

if __name__ == '__main__':
    im = loadImage('A890100080.ACF')
    cutImage(im)
