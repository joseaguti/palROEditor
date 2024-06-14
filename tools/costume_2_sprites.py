import configparser
import json
import numpy as np
import os
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import zipfile
import tqdm
import glob
from googletrans import Translator
import shutil

translator = Translator()

from engine.grf import GRF
from engine.pal import Pal
from engine.sprite import SpriteImage, Action

grf_global = configparser.ConfigParser()
grf_global.read('db/grf_data_const.ini',encoding="euc-kr")

with open('db/jobs.json','r',encoding="euc-kr") as fp:
    jobs = json.load(fp)

with open('db/PCPals.lub','rb') as fp:
    pcpals = fp.read()
pcpals = pcpals.decode('euc-kr')

with open('conf.json','r') as fp:
    config = json.load(fp)

HEAD_COLOR = 200
BODY_COLOR = 400
N_SKINS = 8
NUMBER_HAIRS = 50
sprite_f_sf = grf_global['path']['sprite_f_sf']
sprite_m_sf = grf_global['path']['sprite_m_sf']
OUTPATH = "G:\\blasky_sprites.grf"

fileini = config['ro_ini_file']
new_pal = np.array(config['pal'])
path = os.path.dirname(fileini)
ro_ini = configparser.ConfigParser()
ro_ini.read(fileini, encoding="utf-8")

lines_pal = pcpals.split("\n")
lines_pal = [l for l in lines_pal if not l.startswith("-")]
DB_pal = {}

PATHIN = "D:\\Juegos\\BlackSkyRO\\data\\sprite\\인간족\\몸통"
part_out = "sprite\\인간족\\몸통"
DB = {}
for gender in [sprite_f_sf,sprite_m_sf]:
    pathin = os.path.join(PATHIN,gender,"costume_1")
    files = glob.glob(os.path.join(pathin,"*.*"))
    for file in files:
        filename = os.path.basename(file)
        dirname = os.path.dirname(file)
        part = filename.split("_"+gender)[0]
        try:
            part = translator.translate(part, src='ko', dest='en').text
            part = part.replace(" ","_")
        except:
            pass
        ext = filename.split(".")[1]
        part2 = part + "2"
        key = part2.upper()
        DB[key] = part2
        new_file = part + "2_"+gender+"."+ext
        pathout = os.path.join(OUTPATH,part_out,gender,new_file)
        os.makedirs(os.path.dirname(pathout),exist_ok=True)
        shutil.copy(file,pathout)
        print(file,"->",pathout)

with open('db/costume_2.json','w') as fp:
    json.dump(DB,fp,indent=4)

