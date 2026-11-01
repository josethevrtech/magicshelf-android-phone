#!/usr/bin/env python3
"""Derive an original wider tablet shell from this creation's own phone mesh."""
from pathlib import Path
import struct,math,shutil,json
root=Path(__file__).resolve().parents[1]
source=root/'assets/android-phone';target=root/'assets/android-tablet';target.mkdir(exist_ok=True)
data=bytearray((source/'device.mesh').read_bytes());materials,count=struct.unpack_from('<II',data,4);start=12+materials*16
assert data[:4]==b'DPH2' and len(data)==start+count*32
for n in range(count):
    offset=start+n*32;v=list(struct.unpack_from('<8f',data,offset));v[0]*=5/3
    v[3]/=5/3;length=max(1e-8,math.sqrt(sum(a*a for a in v[3:6])));v[3:6]=[a/length for a in v[3:6]]
    struct.pack_into('<8f',data,offset,*v)
(target/'device.mesh').write_bytes(data)
for p in source.glob('body-*.rgba'):shutil.copy2(p,target/p.name)
(target/'model-info.json').write_text(json.dumps({'name':'Experimental Android tablet','screen':[960,1280],'source':'Original Android Phone geometry, widened 5/3','triangles':count//3},indent=2)+'\n')
print('Experimental tablet mesh:',count//3,'triangles')