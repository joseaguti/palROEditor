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

with open('db/PCPals.lub','rb') as fp:
    pcpals = fp.read()
pcpals  = pcpals.decode('euc-kr')

with open('conf.json','r') as fp:
    config = json.load(fp)

HEAD_COLOR = 200
BODY_COLOR = 400
N_SKINS = 8
NUMBER_HAIRS = 50
sprite_f_sf = grf_global['path']['sprite_f_sf']
sprite_m_sf = grf_global['path']['sprite_m_sf']
OUTPATH = "G:\\blasky_pals.grf"

fileini = config['ro_ini_file']
new_pal = np.array(config['pal'])
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

lines_pal = pcpals.split("\n")
lines_pal = [l for l in lines_pal if not l.startswith("-")]
DB_pal = {}
for line in lines_pal:
    if len(line) == 0:
        continue
    name,value = line.split("=")
    # value is into "" and spaces
    value = value.split('"')[1]
    if name.startswith("[PCIds"):
        name = name.split("[PCIds.")[1].split("]")[0]
        DB_pal[name] = value
    if name.startswith("[PCMounts"):
        name = name.split("[PCMounts.")[1].split("]")[0]
        DB_pal[name] = value

palette_body = grf_global['path']['palette_body']
out_name = "body"
BODY_COLOR_V = 4
skin_ref = np.array([[247, 240, 229, 255],
       [255, 225, 207, 255],
       [255, 198, 178, 255],
       [246, 174, 159, 255],
       [220, 144, 132, 255],
       [189, 115, 107, 255],
       [158,  86,  82, 255],
       [130,  63,  59, 255]], dtype=np.uint8)

skin_ref2 = np.array([[247, 240, 229, 255],
       [255, 225, 207, 255],
       [255, 198, 178, 255],
       [246, 174, 159, 255],
       [220, 144, 132, 255],
       [189, 115, 107, 255],
       [158,  86,  82, 255],
       [130,  63,  59, 255]], dtype=np.uint8)

SKIN_POSITION = {}
for gender in [sprite_f_sf,sprite_m_sf]:
    for k,v in DB_pal.items():
        if v == 'body':
            continue
        v = v.lower()
        SKIN_POSITION[k] = {'sprite':v,'pals':[],'name':[],'type':[],'side':[]}
        for i in range(BODY_COLOR_V):
            name = v + "_" + gender + f"_{i}.pal"
            path = os.path.join(palette_body,name)
            path = path.replace("\\\\", "\\")
            print(path)
            for w in range(len(gp)):
                buffer = gp[w].get_file(path)
                if buffer:
                    break
            if not buffer or len(buffer) < 1024:
                print(f"Error: {path}")
                continue
            pal = Pal(buffer=buffer)
            pal_data = pal.pal
            pal_data[:,:,3] = 255
            flag = False
            for id_,skin_ref_u in enumerate([skin_ref,skin_ref2]):
                for ii in range(pal_data.shape[0]):
                    if np.all(skin_ref_u == pal_data[ii,0:8,:]):
                        SKIN_POSITION[k]["pals"].append(ii)
                        SKIN_POSITION[k]["type"].append(id_)
                        SKIN_POSITION[k]["name"].append(name)
                        SKIN_POSITION[k]["side"].append(0)
                        flag = True
                        break
                if not flag:
                    for ii in range(pal_data.shape[0]):
                        if np.all(skin_ref_u == pal_data[ii,8:16,:]):
                            SKIN_POSITION[k]["pals"].append(ii)
                            SKIN_POSITION[k]["type"].append(id_)
                            SKIN_POSITION[k]["name"].append(name)
                            SKIN_POSITION[k]["side"].append(1)
                            flag = True
                            break
                if flag:
                    break
ñ
for gender in [sprite_f_sf,sprite_m_sf]:
    for k,v in DB_pal.items():
        if v == 'body':
            continue
        v = v.lower()
        if len( SKIN_POSITION[k]["pals"]) < 1:
            continue
        for i in range(BODY_COLOR):
            for ww in [i,BODY_COLOR_V-1]:
                name = v + "_" + gender + f"_{ww}.pal"
                path = os.path.join(palette_body, name)
                path = path.replace("\\\\", "\\")
                print(path)
                for w in range(len(gp)):
                    buffer = gp[w].get_file(path)
                    if buffer:
                        break
                if not buffer or len(buffer) < 1024:
                    continue
                else:
                    break
            if not buffer or len(buffer) < 1024:
                print(f"Error: {path}")
                continue
            pal = Pal(buffer=buffer)
            p = SKIN_POSITION[k]["pals"][-1]
            side = SKIN_POSITION[k]["side"][-1]
            if side == 0:
                skin = pal.pal[p, 0:8, :][None, :, :]
            else:
                skin = pal.pal[p, 8:16, :][None, :, :]
            for x in range(N_SKINS):
                new_skin = new_pal[x, 0:8, :][None, :, :]
                new_skin[:, :, 3] = 255
                if side == 0:
                    pal.pal[p, 0:8, :] = new_skin[0, :, :]
                else:
                    pal.pal[p, 8:16, :] = new_skin[0, :, :]
                new_buffer = b''
                for ii in range(16):
                    for jj in range(16):
                        # c = b''.join([bytes.fromhex(hex(p)) for p in pal[i,j].tolist()])
                        c = pal.pal[ii, jj].tobytes()
                        new_buffer += c
                name = v + "_" + gender + f"_{i + x * BODY_COLOR}.pal"
                path = os.path.join(palette_body, name)
                path = path.replace("\\\\", "\\")
                path = path.replace("data\\", "")
                # path = path.replace("\\", "/")
                path_f = os.path.join(OUTPATH, path)
                os.makedirs(os.path.dirname(path_f), exist_ok=True)
                outname_file = f"{v}_{gender}_{i + x * BODY_COLOR}.pal"
                path_f = os.path.join(os.path.dirname(path_f), outname_file)
                with open(path_f, "wb") as fp:
                    fp.write(new_buffer)
                # print("-->",path,len(new_buffer))
