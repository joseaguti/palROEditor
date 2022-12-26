import os
import configparser
from PIL import Image
from io import BytesIO
from grf import GRF


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRF_DIR = "/opt/update/base"

class GRF_Resource:
    def __init__(self):
        patchs = ClientVersions.objects.filter(type = 1)
        self.grfs_h = list()
        for p in patchs:
            self.grfs_h.append(GRF(GRF_DIR + "/"+p.name, "r"))
        self.conf = self.ConfigSectionMap(BASE_DIR + "/grf_data_const.ini", "path")

    def __del__(self):
        for grf in self.grfs_h:
            del grf

    def ConfigSectionMap(self,file, section):
        dict1 = {}
        Config = configparser.ConfigParser()
        Config.read(file,encoding="utf8")
        options = Config.options(section)
        for option in options:
            try:
                dict1[option] = Config.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1

    def save_cache(self, dest_path,filename, buffer):
        if not os.path.isdir(dest_path):
            os.mkdir(dest_path)
        with open(dest_path + "/" + filename, "wb") as fp:
            fp.write(buffer)

    def restore_cache(self, dest_path,filename):
        try:
            with open(dest_path + "/" + filename, "rb") as fp:
                buffer = fp.read()
            return buffer
        except:
            return None

    def open_grf_file(self,path,filename,default):
        for i in range(0,2):
            for grf in self.grfs_h:
                if grf.check_file(path + filename):
                    buffer = grf.get_file(path + filename)
                    return buffer
            filename = default
        return None
