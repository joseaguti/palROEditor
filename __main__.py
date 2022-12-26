from PyQt5 import QtWidgets, uic,QtGui
from PyQt5.QtWidgets import QLabel, QColorDialog,QDialog, QGraphicsScene
from PyQt5.QtCore import QMetaObject,QObject,QEvent,QPoint,QSize, Qt
from PyQt5.QtCore import pyqtSlot as Slot, pyqtSignal as Signal
from PyQt5.QtGui import QColor, QStandardItem,QStandardItemModel,  QPixmap
import sys
import os
from functools import partial
import re
import configparser
import json
import numpy as np
from itertools import zip_longest
from PIL import Image
from io import BytesIO

from engine.grf import GRF
from engine.pal import Pal
from engine.sprite import SpriteImage, Action


config = configparser.ConfigParser()
config.read('db/grf_data_const.ini',encoding="euc-kr")

with open('db/jobs.json','r',encoding="euc-kr") as fp:
    jobs = json.load(fp)

class ColorLabel(QtWidgets.QLabel):
    class Communicate(QObject):
        s = Signal(QEvent, QPoint, QPoint)

    left_click = None
    doble = None
    right_click = None

    def __init__(self,parent=None):
        self.left_click = ColorLabel.Communicate()
        self.right_click = ColorLabel.Communicate()
        self.doble = ColorLabel.Communicate()
        super().__init__(parent)

    def event(self, e):
        if e.type() == QEvent.Type.MouseButtonPress:
            if e.button() == Qt.LeftButton:
                self.left_click.s.emit(e, e.pos(), self.cursor().pos())
            if e.button() == Qt.RightButton:
                self.right_click.s.emit(e, e.pos(), self.cursor().pos())
        if e.type() == QEvent.Type.MouseButtonDblClick:
            self.doble.s.emit(e, e.pos(), self.cursor().pos())
        return QLabel.event(self, e)


class MainWin(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)

        # Cargamos el archivo .ui
        uic.loadUi("ui/main.ui", self)

        with open("qss/dracula.qss", 'r') as fp:
            css = fp.read()

        self.setStyleSheet(css)
        self.create_palette_grid()

        self.o_pal_ij = [(-1,-1)]
        self.n_pal_ij = [(-1,-1)]
        self.list_grfs = []
        self.gp = []
        self.hair_id = 1
        self.pal_buffer_body = b''
        self.pal_buffer_hair = b''

        self.scene = QGraphicsScene(self)
        self.spritePreview.setScene(self.scene)
        self.load_RO_ini("D:\\Juegos\\BlackSkyRO\\BSRO.ini")

        # Obtenemos una referencia al botón y conectamos la señal "clicked" a una función
        #boton = self.findChild(QtWidgets.QPushButton, "nombre_del_boton")
        #boton.clicked.connect(self.mi_funcion)
        self.init_job_option()
        self.init_sex_option()
        self.jobSel.currentIndexChanged.connect(self.update_pal_list)
        self.genderSel.currentIndexChanged.connect(self.update_pal_list)
        self.Hair_id.valueChanged.connect(self.update_pal_list)

        self.palListHairW.itemClicked.connect(partial(self.pal_sel,'hair'))
        self.palListBodyW.itemClicked.connect(partial(self.pal_sel,'body'))

        self.o2n.clicked.connect(partial(self.move_colors_beetwen_pal,'o2n',False))
        self.n2o.clicked.connect(partial(self.move_colors_beetwen_pal,'n2o',False))
        self.o2n_full.clicked.connect(partial(self.move_colors_beetwen_pal,'o2n',True))
        self.n2o_full.clicked.connect(partial(self.move_colors_beetwen_pal,'n2o',True))

        self.get_name()
        self.update_pal_list()

        self.update_sprite()

    def move_colors_beetwen_pal(self,type_move,full_flag):
        if type_move == 'o2n':
            oring = self.o_pal_ij
            oring_pal = self.o_palette
            dest = self.n_pal_ij
            dest_pal = self.n_palette

        if type_move == 'n2o':
            oring = self.n_pal_ij
            oring_pal = self.n_palette
            dest = self.o_pal_ij
            dest_pal = self.o_palette

        for i in range(len(oring)):
            cell_origing = oring_pal.itemAtPosition(oring[i][0], oring[i][1]).widget()
            cell_dest = dest_pal.itemAtPosition(dest[i][0], dest[i][1]).widget()
            self.set_background_color(cell_dest,self.get_background_color(cell_origing))
        self.recompile_pal()


    def update_sprite(self):
        sprite_path = config['path']['sprite'] + self.sex_sprite_name + '\\\\'\
                      + self.body_sprite_name + "_"+self.sex_sprite_name +".spr"
        act_path = config['path']['sprite'] + self.sex_sprite_name + '\\\\' \
                      + self.body_sprite_name + "_" + self.sex_sprite_name + ".act"
        spr_buffer = self.gp[0].get_file(sprite_path.replace('\\\\','\\'))
        act_buffer = self.gp[0].get_file(act_path.replace('\\\\','\\'))
        spr = SpriteImage(0, 0)
        body_act = Action(act_buffer)
        spr.load_sprite_buffer(spr_buffer,act_buffer)

        if len(self.pal_buffer_body) == 1024:
            spr.palette = self.pal_buffer_body

        body_img = spr.image()

        hair_name = f'{self.hair_id}_{self.sex_sprite_name}'
        sprite_path = config['path']['hair'] + self.sex_sprite_name + '\\\\' + hair_name + ".spr"
        act_path = config['path']['hair'] + self.sex_sprite_name + '\\\\' + hair_name + ".act"
        spr_buffer = self.gp[0].get_file(sprite_path.replace('\\\\', '\\'))
        act_buffer = self.gp[0].get_file(act_path.replace('\\\\', '\\'))
        spr = SpriteImage(0, 0)
        hair_act = Action(act_buffer)
        if spr_buffer and act_buffer:
            spr.load_sprite_buffer(spr_buffer, act_buffer)
        else:
            return False

        if len(self.pal_buffer_hair) == 1024:
            spr.palette = self.pal_buffer_hair

        hair_img = spr.image()
        self.merge_image(body_img,hair_img,body_act,hair_act)

    def recompile_pal(self):
        pal = self.get_pal_original()
        buffer = b''
        for i in range(16):
            for j in range(16):
                #c = b''.join([bytes.fromhex(hex(p)) for p in pal[i,j].tolist()])
                c = pal[i,j].tobytes()
                buffer += c
        if self.last_pal_sel == 'hair':
            self.pal_buffer_hair = buffer
        if self.last_pal_sel == 'body':
            self.pal_buffer_body = buffer
        self.update_sprite()


    def update_pal_list(self):
        self.hair_id = int(self.Hair_id.text())

        files = self.gp[0].get_folder(config['path']['palette_body'] + self.get_name())
        self.palListBodyW.clear()
        for file in files:
            filename = file.split('\\')[-1]
            self.palListBodyW.addItem(filename)
            print(filename)

        hair_name = f'{config["path"]["hair_name"]}{self.hair_id}_{self.sex_sprite_name}_'
        files = self.gp[0].get_folder(config['path']['palette_hair'] + hair_name)
        self.palListHairW.clear()
        for file in files:
            filename = file.split('\\')[-1]
            self.palListHairW.addItem(filename)
            print(filename)

        self.update_sprite()


    def get_name(self):
        index = self.jobSel.currentIndex()
        model = self.jobSel.model()
        item = model.item(index)
        sprite = item.data()
        print(sprite)

        model = self.genderSel.model()
        index = self.genderSel.currentIndex()
        item = model.item(index)

        # Obtenemos el valor asociado al elemento seleccionado
        sex = item.data()
        self.sex_sprite_name = sex
        self.body_sprite_name = sprite

        sname = sprite+"_"+sex
        return sname

    def merge_image(self,body,hair,act_body,act_hair):
        dref = (100,180)
        ref = (20,-100)
        bio_body = BytesIO(body)
        bio_hair = BytesIO(hair)

        body_pil = Image.open(bio_body)
        hair_pil = Image.open(bio_hair)

        w = body_pil.width
        h = body_pil.height + hair_pil.height

        complete_pil = Image.new("RGBA",(200,200))

        layer_pos_body = act_body.actions[0]['animations'][0]['layers'][0]['pos']
        layer_pos_hair = act_hair.actions[0]['animations'][0]['layers'][0]['pos']

        pos_body_x = act_body.actions[0]['animations'][0]['pos'][0]['x']
        pos_body_y = act_body.actions[0]['animations'][0]['pos'][0]['y']

        pos_hair_x = act_hair.actions[0]['animations'][0]['pos'][0]['x']
        pos_hair_y = act_hair.actions[0]['animations'][0]['pos'][0]['y']

        x_h = dref[0] - hair_pil.width // 2 + layer_pos_hair[0] + ref[0] - pos_hair_x
        y_h = dref[1] - hair_pil.height // 2 + layer_pos_hair[1] + ref[1] - pos_hair_y

        x_b = dref[0] - body_pil.width // 2 + layer_pos_body[0]  + ref[0] - pos_body_x
        y_b = dref[1] - body_pil.height // 2 + layer_pos_body[1] + ref[1]  - pos_body_y

        complete_pil.paste(body_pil, (x_b, y_b),body_pil)
        complete_pil.paste(hair_pil, (x_h, y_h), hair_pil)

        buffer_out = BytesIO()
        complete_pil.save(buffer_out,"PNG")

        self.put_image(buffer_out.getvalue())

    def put_image(self,buffer):
        pixmap = QPixmap()
        pixmap.loadFromData(buffer)
        self.scene.clear()
        self.scene.addPixmap(pixmap)


    def pal_sel(self,type_pal):
        global config
        print(type_pal)
        if type_pal == 'hair':
            pal = self.palListHairW.currentItem().text()
            print(pal)
            pal_path = config['path']['palette_hair'] + pal
        if type_pal == 'body':
            pal = self.palListBodyW.currentItem().text()
            print(pal)
            pal_path = config['path']['palette_body'] + pal

        print(pal_path)
        self.last_pal_sel = type_pal
        buffer = self.gp[0].get_file(pal_path.replace('\\\\','\\'))

        if type_pal == 'body':
            self.pal_buffer_body = buffer
        if type_pal == 'hair':
            self.pal_buffer_hair = buffer

        pal = Pal(buffer=buffer)
        self.set_pal_original(pal.pal)

        self.update_sprite()



    def init_job_option(self):
        global jobs
        model = QStandardItemModel()
        self.jobSel.setModel(model)
        for job in jobs['rows']:
            item = QStandardItem(job['job_name'])
            item.setData(job['sprite'])
            model.appendRow(item)

        #self.jobSel

    def init_sex_option(self):
        global config
        model = QStandardItemModel()
        self.genderSel.setModel(model)
        item = QStandardItem('F')
        item.setData(config['path']['sprite_f_sf'])
        model.appendRow(item)
        item = QStandardItem('M')
        item.setData(config['path']['sprite_m_sf'])
        model.appendRow(item)



    def get_background_color(self,cell):
        match = re.search(r"background-color : #[a-fA-F0-9]{6};", cell.styleSheet())
        hex_color = match.string[match.start() + 19:match.end() - 1]
        return hex_color

    def set_background_color(self,cell,color):
        if type(color) is str:
            hex_color = color
        else:
            hex_color = "".join([hex(c).split('0x')[-1].zfill(2) for c in color])

        if hex_color[0] != '#':
            hex_color = '#'+hex_color
        current_style_sheet = cell.styleSheet()
        new_style_sheet = re.sub(r"background-color : #[a-fA-F0-9]{6};", f" background-color : {hex_color};",
                                 current_style_sheet)
        cell.setStyleSheet(new_style_sheet)

    def change_color(self,type_pal,i,j):
        if type_pal == "original":
            cell = self.o_palette.itemAtPosition(i, j).widget()
        if type_pal == "new":
            cell = self.n_palette.itemAtPosition(i, j).widget()
        hex_color = self.get_background_color(cell)
        c_color = QColor(hex_color)
        color_dialog = QColorDialog(self)
        color_dialog.setCurrentColor(c_color)
        if color_dialog.exec_() == QDialog.Rejected:
            # Si se ha pulsado el botón "Cancelar", no hacemos nada
            return
        # Si no se ha pulsado el botón "Cancelar", obtenemos el color seleccionado
        color = color_dialog.selectedColor()
        print(color, color.name())
        if color is not None and len(color.name()) > 0:
            self.set_background_color(cell, color.name())

        self.recompile_pal()


    def select_cell(self,type_pal,i,j,row):
        if type_pal == "original":
            palette = self.o_palette
            self.o_pal_ij = []
            pal_ij = self.o_pal_ij
        else:
            palette = self.n_palette
            self.n_pal_ij = []
            pal_ij = self.n_pal_ij


        for w in range(16):
            for k in range(16):
                cell_o = palette.itemAtPosition(w,k).widget()
                current_style_sheet = cell_o.styleSheet()
                new_style_sheet = re.sub(r"border : \dpx", "border : 0px",
                                         current_style_sheet)
                cell_o.setStyleSheet(new_style_sheet)


        if not row:
            cell = palette.itemAtPosition(i, j).widget()
            current_style_sheet = cell.styleSheet()
            new_style_sheet = re.sub(r"border : \dpx solid (red|blue);", "border : 2px solid red;",
                                     current_style_sheet)
            cell.setStyleSheet(new_style_sheet)
            pal_ij.append((i, j))
        else:
            jj = j // 8
            for j in range(jj*8,(jj+1)*8):
                cell = palette.itemAtPosition(i, j).widget()
                current_style_sheet = cell.styleSheet()
                new_style_sheet = re.sub(r"border : \dpx solid (red|blue);", "border : 2px solid blue;",
                                         current_style_sheet)
                cell.setStyleSheet(new_style_sheet)
                pal_ij.append((i,j))



    def load_RO_ini(self,fileini):
        path = os.path.dirname(fileini)
        ro_ini = configparser.ConfigParser()
        ro_ini.read(fileini, encoding="utf-8")
        list_grfs = []
        for i in range(9):
            if f"{i}" not in ro_ini['Data']:
                break
            list_grfs.append(os.path.join(path,ro_ini["Data"][f"{i}"]))


        self.list_grfs = list_grfs[::-1]
        print(self.list_grfs)

        for grf_name in self.list_grfs:
            grf = GRF(grf_name)
            self.gp.append(grf)



    def create_palette_grid(self):
        for i in range(16):
            for j in range(16):
                ih = hex(i)[-1].upper()
                jh = hex(j)[-1].upper()
                cell = ColorLabel(self)
                # cell.setText(f"C{ih}{jh}")
                cell.setText('')
                cell.setStyleSheet(f"QLabel {{ background-color : #000000; color : blue; border : 0px solid red; }}")

                cell.left_click.s.connect(partial(self.select_cell,'original',i,j,False))
                cell.right_click.s.connect(partial(self.select_cell,'original',i,j,True))
                cell.doble.s.connect(partial(self.change_color,'original',i,j))
                self.o_palette.addWidget(cell,i,j)

                cell = ColorLabel( self)
                # cell.setText(f"C{ih}{jh}")
                cell.setText('')
                cell.setStyleSheet(f"QLabel {{ background-color : #000000; color : blue; border : 0px solid red; }}")
                cell.left_click.s.connect(partial(self.select_cell, 'new', i, j,False))
                cell.right_click.s.connect(partial(self.select_cell,'new',i,j,True))
                cell.doble.s.connect(partial(self.change_color, 'new', i, j))
                self.n_palette.addWidget(cell, i, j)


    def set_pal_original(self,pal):
        for i in range(16):
            for j in range(16):
                cell = self.o_palette.itemAtPosition(i,j).widget()
                pal_item = pal[i,j,:3].tolist()
                self.set_background_color(cell,pal_item)

    def grouper(self,iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=fillvalue)

    def get_pal_original(self):
        pal = np.zeros((16,16,4),dtype=np.uint8)
        for i in range(16):
            for j in range(16):
                cell = self.o_palette.itemAtPosition(i, j).widget()
                hexcolor = self.get_background_color(cell)
                color = [int(hexcolor[1:3],16), int(hexcolor[3:5],16), int(hexcolor[5:7],16),int('00',16)]
                pal[i,j,:] = color
        return pal


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mc = MainWin()
    mc.show()

    file = "test/결혼_남_0.pal"
    pal = Pal(file)
    print('Set palette')
    #mc.set_pal_original(pal.pal)
    #spr = SpriteImage(0,0)
    #spr.load_sprite_files('test/성투사_여.spr','test/성투사_여.act')
    #mc.put_image(spr.image())

    folders = mc.gp[0].get_folder(config['path']['palette_body']+mc.get_name())
    print(folders)

    app.exec()

