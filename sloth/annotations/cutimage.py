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
    themax = 0L
    firstcut = 0
    for i in range(im.shape[0]-1):
        difsum = 0L
        for j in range(im.shape[1]):
            for k in range(im.shape[2]):
                difsum += abs(im[i, j, k] - im[i+1, j, k])
        if difsum >= themax:
            themax = difsum
            firstcut = i
    print(themax)
    print(firstcut)
