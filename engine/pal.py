import numpy as np
from struct import unpack

class Pal():

    def __init__(self,file = None,buffer = None):

        if buffer is not None:
            self.buffer = buffer
        if file is not None:
            with open(file,'rb') as fp:
                self.buffer = fp.read()

        self.pal = np.zeros((16,16,4),dtype=np.uint8)
        self.decode_file()

    def decode_file(self):
        for i in range(256):
            r,g,b,a = unpack("BBBB",self.buffer[i*4:(i+1)*4])
            x = i // 16
            y = i % 16
            self.pal[x,y,:] = [r,g,b,a]