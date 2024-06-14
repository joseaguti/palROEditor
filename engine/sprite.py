import os
import configparser
from PIL import Image
from struct import *
import numpy as np

try:
    from StringIO import BytesIO
except ImportError:
    from io import BytesIO
#from grf import GRF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Con esta clase se accede a los sprites de los GRF
'''
type:
    "hat" -> Sprite de un gorro
    "hair" -> Sprite de un pelo. Se puede especificar en kwargs 'pal_id' y 'gender'
    "body" -> Sprite del cuerpo de un job. Se puede especificar en kwargs 'pal_id' y 'gender'
    'mob' -> Sprite de un mob

act_id -> Id del act
frame -> nº de frame del act
'''


class Action:
    def __init__(self, buffer):
        self.actions = list()
        self.version = 0.0
        self.sounds = list()
        self.act_header = dict()
        self.load_act(buffer)

    def readLayers(self, buffer):
        layers = list()
        pointer = 0
        count = unpack("I", buffer[pointer:pointer + 4])[0]
        pointer += 4
        version = self.act_header['version']
        # print(str(count) + " capas... (version " + str(version) + ")")
        for i in range(0, count):
            x, y, index, is_mirror = unpack("iiii", buffer[pointer:pointer + 16])
            r, g, b, a = 255.0, 255.0, 255.0, 255.0
            scale1, scale2 = 1.0, 1.0
            angle = 0
            spr_type = 0
            width, height = 0, 0
            pointer += 16
            if version < 2.0:
                size = 0
            elif version < 2.4:
                size = 16
                r, g, b, a = unpack("BBBB", buffer[pointer:pointer + 4])
                pointer += 4
                scale1 = unpack("f", buffer[pointer:pointer + 4])
                scale2 = scale1
                pointer += 4
                angle = unpack("I", buffer[pointer:pointer + 4])[0]
                pointer += 4
                spr_type = unpack("I", buffer[pointer:pointer + 4])[0]
                pointer += 4
            elif version == 2.4:
                size = 20
                r, g, b, a = unpack("BBBB", buffer[pointer:pointer + 4])
                pointer += 4
                scale1, scale2 = unpack("ff", buffer[pointer:pointer + 8])
                pointer += 8
                angle = unpack("I", buffer[pointer:pointer + 4])[0]
                pointer += 4
                spr_type = unpack("I", buffer[pointer:pointer + 4])[0]
                pointer += 4
            else:
                size = 28
                r, g, b, a = unpack("BBBB", buffer[pointer:pointer + 4])
                pointer += 4
                scale1, scale2 = unpack("ff", buffer[pointer:pointer + 8])
                pointer += 8
                angle = unpack("I", buffer[pointer:pointer + 4])[0]
                pointer += 4
                spr_type = unpack("I", buffer[pointer:pointer + 4])[0]
                pointer += 4
                width, height = unpack("II", buffer[pointer:pointer + 8])
                pointer += 8

            layer = {
                "pos": (x, y),
                "index": index,
                "is_mirror": is_mirror,
                "scale": (scale1, scale2),
                "color": (r / 255.0, g / 255.0, b / 255.0, a / 255.0),
                "angle": angle,
                "spr_type": spr_type,
                "width": width,
                "height": height
            }

            layers.append(layer)

        # print(layers)
        sound = -1
        if version >= 2.0:
            sound = unpack("i", buffer[pointer:pointer + 4])[0]
            pointer += 4
        # print("Sonido "+ str(sound))
        pos = [{'x': 0, 'y': 0}]
        if version >= 2.3:
            count = unpack("I", buffer[pointer:pointer + 4])[0]
            # print("Posiciones:  " + str(count))
            pointer += 4
            if count > 0:
                pos = list()
            for i in range(0, count):
                unk, x, y, attr = unpack("iiii", buffer[pointer:pointer + 16])
                pointer += 16
                pos.append({'unk': unk, 'x': x, 'y': y, 'attr': attr})
            # print(pos)
        # print(pointer)
        return {'layers': layers, 'sound': sound, 'pos': pos}, pointer

    def readAnimations(self, buffer):
        animations = list()
        pointer = 0
        count = unpack('I', buffer[pointer:pointer + 4])[0]
        # print(str(count) + " animaciones...")
        pointer += 4
        for i in range(0, count):
            pointer += 32
            animation, p_s = self.readLayers(buffer[pointer:])
            # print("Desplazo "+str(p_s))
            pointer += p_s
            animations.append(animation)
        return animations, pointer

    def readActions(self, buffer):
        count = unpack('h', buffer[:2])[0]
        pointer = 12
        # print(str(count) + " acciones...")
        for i in range(0, count):
            animations, p_s = self.readAnimations(buffer[pointer:])
            pointer += p_s
            action = {
                'animations': animations,
                'delay': 150}
            self.actions.append(action)
            # raise(Exception("Para pls"))
        return pointer

    def load_act(self, buffer):
        pointer = 0
        self.act_header['head'] = unpack('<2s', buffer[pointer:pointer + 2])
        pointer = 2
        version_1, version_2 = unpack('BB', buffer[pointer:pointer + 2])
        pointer = 4
        self.act_header['version'] = float(version_1) / 10.0 + float(version_2)
        self.version = self.act_header['version']

        # if version < 2.0:
        #     layer_size = 16
        # elif version < 2.4:
        #     layer_size = 32
        # elif version == 2.4:
        #     layer_size = 36
        # else:
        #     layer_size = 44
        #
        # action_count = unpack('h', buffer[pointer:pointer + 2])[0]
        # pointer += 12
        # for i in range(0,action_count):
        #     animation_count = unpack('i', buffer[pointer:pointer + 4])
        #     for j in range(0,animation_count):
        #         pointer += 32
        #         layer_count = unpack('i', buffer[pointer:pointer + 4])
        #         pointer += layer_count*layer_size
        #         if version >= 2.0:
        #             pointer += 4
        #         else:
        #             pos_count = unpack('i', buffer[pointer:pointer + 4])
        #             pointer += pos_count*16

        p_s = self.readActions(buffer[pointer:])
        pointer += p_s

        if self.version >= 2.1:
            # Sound
            count = unpack('I', buffer[pointer:pointer + 4])[0]
            pointer += 4
            for i in range(0, count):
                sound = unpack("<40s", buffer[pointer:pointer + 40])
                pointer += 40
                self.sounds.append(sound)
        if self.version >= 2.2:
            # Delay
            for action in self.actions:
                action['delay'] = unpack('f', buffer[pointer:pointer + 4]) * 25
                pointer += 4


class SpriteImage():
    def __init__(self, type, id, **kwargs):
        self.id = id
        self.type = type
        self.pal_id = int(kwargs['pal_id']) if 'pal_id' in kwargs else 0
        self.gender = kwargs['sex'] if 'sex' in kwargs else 'F'
        self.act_id = int(kwargs['act_id']) if 'act_id' in kwargs else 0
        self.frame = int(kwargs['frame']) if 'frame' in kwargs else 0
        self.frames_data = list()
        self.sprite_header = dict()
        self.load_sprite()
        self.background_color = (0, 0, 0)
        self.actions = list()

    def load_sprite_files(self,file_spr,file_act):
        with open(file_spr,'rb') as fp:
            buffer_sprite = fp.read()
        with open(file_act, 'rb') as fp:
            buffer_act = fp.read()
        self.background_color = (200, 248, 211)
        self.parse_sprite(buffer_sprite)
        self.actions = Action(buffer_act).actions

    def load_sprite_buffer(self, buffer_sprite, buffer_act):
        self.background_color = (200, 248, 211)
        self.parse_sprite(buffer_sprite)
        self.actions = Action(buffer_act).actions

    def load_sprite(self):
        if self.type == "hat":
            view = client_db.viewDb.get_by_id(self.id)
            path_in = self.conf['sprite_f'] if self.gender == 'F' else self.conf['sprite_m']
            pref = self.conf['sprite_f_sf'] if self.gender == 'F' else self.conf['sprite_m_sf']
            name_sprite = pref + view.sprite_name + ".spr"
            name_act = pref + view.sprite_name + ".act"
            buffer_sprite = super().open_grf_file(path_in, name_sprite, "")
            buffer_act = super().open_grf_file(path_in, name_act, "")
            self.background_color = (200, 248, 211)
            self.parse_sprite(buffer_sprite)
            self.actions = Action(buffer_act).actions
        elif self.type == 'hair':
            path_in = self.conf['hair_f'] if self.gender == 'F' else self.conf['hair_m']
            pref = self.conf['hair_f_sf'] if self.gender == 'F' else self.conf['hair_m_sf']
            name_sprite = str(self.id) + "_" + pref + ".spr"
            name_act = str(self.id) + "_" + pref + ".act"
            buffer_sprite = super().open_grf_file(path_in, name_sprite, "")
            buffer_act = super().open_grf_file(path_in, name_act, "")
            self.background_color = (200, 248, 211)
            self.parse_sprite(buffer_sprite)
            self.actions = Action(buffer_act).actions

    def readRgbaImage(self, buffer):
        pointer = 0
        for i in range(0, self.sprite_header['rgba_index']):
            frame = dict()
            frame['width'], frame['height'] = unpack("hh", buffer[pointer:pointer + 4])
            frame['type'] = 'rgba'
            frame['offset'] = pointer
            pointer += 4
            pointer_end = frame['width'] * frame['height'] * 4
            frame['data'] = buffer[pointer:pointer + pointer_end]
            pointer += pointer_end
            self.frames_data.append(frame)

        return pointer

    def readIndexedImage(self, buffer):
        pointer = 0
        for i in range(0, self.sprite_header['indexed_count']):
            frame = dict()
            frame['width'], frame['height'] = unpack("hh", buffer[pointer:pointer + 4])
            frame['type'] = 'indexed'
            frame['offset'] = pointer
            pointer += 4
            pointer_end = frame['width'] * frame['height']
            frame['data'] = buffer[pointer:pointer + pointer_end]
            pointer += pointer_end
            self.frames_data.append(frame)
        return pointer

    def readIndexedImageRLE(self, buffer):
        pointer = 0
        for i in range(0, self.sprite_header['indexed_count']):
            frame = dict()
            frame['width'], frame['height'], frame['size'] = unpack("hhh", buffer[pointer:pointer + 6])
            frame['type'] = 'indexed_rle'
            frame['offset'] = pointer
            pointer += 6
            pointer_end = frame['size']
            frame['data'] = buffer[pointer:pointer + pointer_end]
            pointer += pointer_end
            self.frames_data.append(frame)
        return pointer

    '''
    Esta codificación es un zip cutre. 
    Cuando hay muchos ceros seguidos que corresponde al background en vez de ponerlos todos
    pone un 0 y el numero de ceros que hay a continuación.
    '''

    def RLE_decode(self, frame):
        frame['type'] = 'indexed'
        data = frame['data']
        index = 0
        size = frame['size']
        data_new = b""

        while index < size:
            b1 = data[index:index + 1]
            index += 1
            data_new += b1
            if b1 == b'\x00':
                b2 = data[index:index + 1]
                index += 1
                if b2 == b'\x00':
                    data_new += b2
                else:
                    count = ord(b2)
                    for i in range(0, count - 1):
                        data_new += b1

        # print(data_new.__len__(),size,frame['width']*frame['height'])
        frame['data'] = data_new
        return frame

    def Indexed_decode(self, frame):
        frame['type'] = 'rgba'
        data = frame['data']
        w = frame['width']
        h = frame['height']
        image = np.zeros((h, w, 4))
        for i in range(0, h):
            for j in range(0, w):
                index = i * w + j
                b = data[index]
                # Indice 0 es background
                if b == 0:
                    image[i, j, 0] = 255
                    image[i, j, 1] = 255
                    image[i, j, 2] = 255
                    image[i, j, 3] = 0
                else:
                    red, green, blue, alpha = unpack("BBBB", self.palette[4 * b:4 * b + 4])
                    image[i, j, 0] = red
                    image[i, j, 1] = green
                    image[i, j, 2] = blue
                    image[i, j, 3] = 255

        frame['image'] = np.uint8(image)
        return frame

    def parse_sprite(self, buffer):

        pointer = 0
        self.sprite_header['head'] = unpack('<2s', buffer[pointer:pointer + 2])
        pointer = 2
        version_1, version_2 = unpack('BB', buffer[pointer:pointer + 2])
        pointer = 4
        self.sprite_header['version'] = float(version_1) / 10.0 + float(version_2)
        self.sprite_header['indexed_count'] = unpack('h', buffer[pointer:pointer + 2])[0]
        self.sprite_header['rgba_index'] = self.sprite_header['indexed_count']
        pointer = 6

        if self.sprite_header['version'] > 1.1:
            self.sprite_header['rgba_count'] = unpack('h', buffer[pointer:pointer + 2])[0]
            pointer = 8

        if self.sprite_header['version'] > 2.1:
            pointer += self.readIndexedImage(buffer[pointer:])
        else:
            pointer += self.readIndexedImageRLE(buffer[pointer:])

        if self.sprite_header['version'] > 1.1:
            self.palette = buffer[pointer:1024 + pointer]
            self.palette_pos = pointer

    def image(self):
        f = self.frames_data[self.frame]
        if f['type'] == 'indexed_rle':
            f = self.RLE_decode(f)
        if f['type'] == 'indexed':
            f = self.Indexed_decode(f)
        img = Image.fromarray(f['image'])
        with BytesIO() as output:
            img.save(output, "PNG")
            buffer_out = output.getvalue()

        return buffer_out


