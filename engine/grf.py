from struct import *
import zlib
import re

class grf_header(object):
    signature = ""
    key = ""
    table_offset = 0
    seeds = 0
    filecount = 0
    version = 0

class GRF:
    HEADER_SIZE = 46
    f = None
    loaded = False
    sizeTable = 0
    fileTable = ""
    header = grf_header()
    filename = ""

    def __init__(self, filename = None,mode = "r"):
        if filename is not None:
            self.open(filename,mode)

    def open(self,filename,mode):
        try:
            self.f = open(filename,mode+"b")
        except Exception as e:
            print(e)
            print("GRF : Error al abrir "+filename)
            return False
        try:
            header = self.f.read(self.HEADER_SIZE)
            # unpack("a15signature/a15key/Ltable_offset/Lseeds/Lfilecount/Lversion", header)
            self.header.signature = unpack('<15s', header[0:15])
            self.header.key = unpack('<15s', header[15:30])
            self.header.table_offset,self.header.seeds,\
                self.header.filecount,self.header.version = unpack('IIII', header[30:])

            self.f.seek(self.HEADER_SIZE + self.header.table_offset)
            pack_size, real_size = unpack("II", self.f.read(8))
            self.sizeTable = pack_size
            table_zip = self.f.read(pack_size)
            self.fileTable = zlib.decompress(table_zip)
            self.fileList = self.decode_fileTable()
            self.loaded = True
            self.filename = filename
            return True
        except:
            print("GRF : Error al procesar " + filename)
            return False

    def __del__(self):
        if self.loaded:
            self.f.close()

    def decode_fileTable(self):
        s = b'data\\'
        files = self.fileTable.split(s)
        files = ["data\\"+file.split(b'\0')[0].decode('euc-kr',errors='ignore') for file in files]
        return files

    def get_folder(self,folder):
        # (\\.*)
        if folder[-1] == '\\':
            folder = folder[:-1]
        reg = r"^{}.*".format(folder)
        print(reg)
        regex = re.compile(reg)
        files_filter = sorted([item for item in  self.fileList if regex.match(item)])
        return files_filter


    def get_file(self,file):
        if not self.loaded:
            return False
        try:
            file_enc = file.encode('euc-kr')+b'\0'
            if file_enc not in self.fileTable:
                return False
            pos = self.fileTable.index(file_enc)
        except ValueError:
            return False
        pos += file.encode('euc-kr').__len__() + 1
        pack_size,length_aligned,real_size,flags = unpack("IIIb",self.fileTable[pos:pos+13])
        position = unpack("I",self.fileTable[pos+13:pos+17])[0]
        self.f.seek(self.HEADER_SIZE + position)
        file_zip = self.f.read(pack_size)
        return zlib.decompress(file_zip)

    def check_file(self,file):
        if not self.loaded:
            return False
        if type(file) is not str and type(file) is not bytes:
            print("formato raro",type(file))
            return False
        try:
            file_enc = file.encode('euc-kr') + b'\0'
            if file_enc not in self.fileTable:
                return False
            self.fileTable.index(file_enc)
            return True
        except ValueError as e:
            print(e)
            return False


if __name__ == "__main__":
    fgrf = GRF("test.grf","r")
    fgrf.fileTable
    print(fgrf.check_file(b"data\\luafiles514\\lua files\\datainfo\\accname.lub"))
