import zipfile

zp = zipfile.ZipFile('test.zip',mode='a')

buffer = b'1234abc\x01'

zp.writestr('data/악세사리/test.bin',buffer)

zp.close()