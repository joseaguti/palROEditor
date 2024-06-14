
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
import glob

PATH_0 = "D:\Juegos\BlackSkyRO\data\sprite\악세사리\남"
PATH_1 = "D:\Juegos\BlackSkyRO\data\sprite\악세사리\여"

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


OUTPATH = "G:\\blasky_sprites.grf\\sprite\\악세사리"
new_pal = np.array(config['pal'])
path_hair = grf_global['path']['palette_hair']
sprite_f_sf = grf_global['path']['sprite_f_sf']
sprite_m_sf = grf_global['path']['sprite_m_sf']
hair_name = grf_global['path']['hair_name']

names = ['ears_0','ears_1','ears_2','ears_3']
gender = ['남', '여']
for g,PATH in enumerate([PATH_0, PATH_1]):
    files = sorted(glob.glob(PATH + "\*.spr"))

    for i,file in enumerate(files):
        spr = SpriteImage(0, 0)
        with open(file, 'rb') as fp:
            spr_buffer = fp.read()
        file_act = file.replace(".spr", ".act")
        with open(file_act, 'rb') as fp:
            act_buffer = fp.read()
        body_act = Action(act_buffer)
        spr.load_sprite_buffer(spr_buffer, act_buffer)
        pal = spr.palette
        pal_np = np.frombuffer(pal, dtype=np.uint8).reshape((16, 16, 4)).copy()
        for x in range(N_SKINS):
            new_skin = new_pal[x, 0:8, :][None, :, :]
            new_skin[:, :, 3] = 255
            pal_np[8, 0:8, :] = new_skin[0, :, :]
            new_buffer = b''
            for ii in range(16):
                for jj in range(16):
                    # c = b''.join([bytes.fromhex(hex(p)) for p in pal[i,j].tolist()])
                    c = pal_np[ii, jj].tobytes()
                    new_buffer += c
            # Convertir a bytearray para permitir modificaciones
            spr_buffer = bytearray(spr_buffer)
            spr_buffer[spr.palette_pos:spr.palette_pos + 1024] = new_buffer
            # Si necesitas convertir de vuelta a bytes después de la modificación
            spr_buffer = bytes(spr_buffer)

            outpath = OUTPATH+"\\"+gender[g]
            os.makedirs(outpath, exist_ok=True)
            name_out = f"{gender[g]}_{names[i]}_{x}"
            with open(outpath+"\\"+name_out+".spr", 'wb') as fp:
                fp.write(spr_buffer)
            with open(outpath+"\\"+name_out+".act", 'wb') as fp:
                fp.write(act_buffer)

# INSERT SQL

query = "INSERT INTO `view_db` (`name`, `sprite_name`) VALUES\n"
for name in names:
    for i in range(N_SKINS):
        query += "('" + name + f"_{i}" + "', '_" + name + f"_{i}" + "'),\n"

query = query[:-2] + ";"
print(query)