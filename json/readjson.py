import json
import os
from PIL import Image

def doencode(a):
    out = dict()
    for key, value in a.items():
        akey = key.encode('utf-8')
        if isinstance(value, int):
            avalue = str(value)
        else:
            avalue = value.encode('utf-8')
        out[akey] = avalue
    return out

files = os.listdir('.')

out = []

for filename in files:
    if os.path.splitext(filename)[1] == '.json':
        f = open(filename, 'r')
        f = json.load(f)
        patientinf = f['patient_info']
        # patientinf = doencode(patientinf)
        endoscopyinfo = f['endoscopy_info']
        endoscopyinfo = doencode(endoscopyinfo)
        pathologyinfo = f['pathology_info']
        fname = f['file_path'].replace('\\', '/')
        image = {
            'annotations': [],
            'class': 'image',
            'filename': fname,
            'md5': '',
            'time': [],
            'patientinf': patientinf,
            'endoscopyinfo': endoscopyinfo,
            'pathologyinfo': pathologyinfo
        }
        out.append(image)

f = open('out.json', 'w')
json.dump(out, f, indent=4, separators=(',', ': '), sort_keys=True)
f.write("\n")
