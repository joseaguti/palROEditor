import configparser
import json
import numpy as np
import os
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import zipfile
import tqdm

from engine.grf import GRF
from engine.pal import Pal
from engine.sprite import SpriteImage, Action


grf_global = configparser.ConfigParser()
grf_global.read('db/grf_data_const.ini',encoding="euc-kr")

with open('db/jobs.json','r',encoding="euc-kr") as fp:
    jobs = json.load(fp)

with open('conf.json','r') as fp:
    config = json.load(fp)

HEAD_COLOR = 200
BODY_COLOR = 400
N_SKINS = 8
NUMBER_HAIRS = 50

fileini = config['ro_ini_file']
path = os.path.dirname(fileini)
ro_ini = configparser.ConfigParser()
ro_ini.read(fileini, encoding="utf-8")
list_grfs = []
for i in range(9):
    if f"{i}" not in ro_ini['Data']:
        continue
    list_grfs.append(os.path.join(path, ro_ini["Data"][f"{i}"]))


gp = []
for grf_name in list_grfs:
    grf = GRF(grf_name)
    gp.append(grf)


OUTPATH = "G:\\blasky_pals.grf"
new_pal = np.array(config['pal'])
path_hair = grf_global['path']['palette_hair']
sprite_f_sf = grf_global['path']['sprite_f_sf']
sprite_m_sf = grf_global['path']['sprite_m_sf']
hair_name = grf_global['path']['hair_name']



for gender in [sprite_f_sf,sprite_m_sf]:
    for i in tqdm.tqdm(range(HEAD_COLOR)):
        for j in range(NUMBER_HAIRS):
            name = hair_name+f"{j}_"+gender+f"_{i}.pal"
            path = os.path.join(path_hair,name)
            path = path.replace("\\\\", "\\")
            #path = path.replace("\\","/")
            buffer = b''

            for w in range(len(gp)):
                buffer = gp[w].get_file(path)
                if buffer:
                    break
            if not buffer or len(buffer) < 1024:
                print(f"Error: {path}")
                continue
            #print(path,len(buffer))
            pal = Pal(buffer=buffer)
            skin = pal.pal[8,0:8,:][None,:,:]
            for x in range(N_SKINS):
                new_skin = new_pal[x,0:8,:][None,:,:]
                new_skin[:,:,3]  = 255
                pal.pal[8, 0:8, :] = new_skin[0,:,:]
                new_buffer = b''
                for ii in range(16):
                    for jj in range(16):
                        # c = b''.join([bytes.fromhex(hex(p)) for p in pal[i,j].tolist()])
                        c = pal.pal[ii, jj].tobytes()
                        new_buffer += c
                name = hair_name + f"{j}_" + gender + f"_{i+x*HEAD_COLOR}.pal"
                path = os.path.join(path_hair, name)
                path = path.replace("\\\\", "\\")
                path = path.replace("data\\", "")
                #path = path.replace("\\", "/")
                path_f = os.path.join(OUTPATH, path)
                os.makedirs(os.path.dirname(path_f),exist_ok=True)
                with open(path_f,"wb") as fp:
                    fp.write(new_buffer)
                #print("-->",path,len(new_buffer))

jobs_sprites = [j['sprite'] for j in jobs['rows']]
palette_body = grf_global['path']['palette_body']


for gender in [sprite_f_sf,sprite_m_sf]:
    for job in tqdm.tqdm(jobs_sprites):
        if job is None:
            continue
        for i in range(BODY_COLOR):
            name = job+"_"+gender+f"_{i}.pal"
            path = os.path.join(palette_body,name)
            path = path.replace("\\\\", "\\")
            #path = path.replace("\\","/")
            buffer = b''
            for w in range(len(gp)):
                buffer = gp[w].get_file(path)
                if buffer:
                    break
            if not buffer or len(buffer) < 1024:
                print(f"Error: {path}")
                continue
           # print(path,len(buffer))
            pal = Pal(buffer=buffer)
            skin = pal.pal[8,0:8,:][None,:,:]
            for x in range(N_SKINS):
                new_skin = new_pal[x, 0:8, :][None, :, :]
                new_skin[:, :, 3] = 255
                pal.pal[8, 0:8, :] = new_skin[0, :, :]
                new_buffer = b''
                for ii in range(16):
                    for jj in range(16):
                        # c = b''.join([bytes.fromhex(hex(p)) for p in pal[i,j].tolist()])
                        c = pal.pal[ii, jj].tobytes()
                        new_buffer += c
                name = job + "_"+gender+f"_{i+x*BODY_COLOR}.pal"
                path = os.path.join(palette_body, name)
                path = path.replace("\\\\", "\\")
                path = path.replace("data\\","")
                #path = path.replace("\\", "/")
                path_f = os.path.join(OUTPATH, path)
                os.makedirs(os.path.dirname(path_f), exist_ok=True)
                with open(path_f, "wb") as fp:
                    fp.write(new_buffer)
                #print("-->",path,len(new_buffer))