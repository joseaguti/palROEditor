from engine.pal import Pal
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

file = "test/결혼_남_0.pal"
pal = Pal(file)

(f,ax) = plt.subplots()
ax.imshow(pal.pal[:,:,:3])