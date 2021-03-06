import sys
import numpy as np
import matplotlib.pyplot as plt

SIZE = 15
plt.rc('font', size=SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=SIZE)     # fontsize of the x and y labels
plt.rc('xtick', labelsize=SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SIZE)    # legend fontsize
plt.rc('figure', titlesize=SIZE)  # fontsize of the figure title

x = [0, 10, 20, 30, 40]
dataRaw = np.load(sys.path[0] + "/complete_results.npy")
data = dataRaw[:,0,:]

y = np.mean(data, axis=1)
std = np.std(data, axis=1)

fig, ax = plt.subplots()
plt.ylim(ymin = 0, ymax = 10)
ax.bar(x, y,
       yerr=std,
       align='center',
       color=('#1f77b4'),
       ecolor='black',
       width=7,
       capsize=15)

ax.set_xlabel('Timeslot length (ms)')
ax.set_ylabel('Completion time (s)')
ax.set_xticks(x)
ax.yaxis.grid(True)

SAVE = True
if SAVE:
    plt.savefig(sys.path[0] + "/time8.pdf", dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches='tight', pad_inches=0,
                frameon=None, metadata=None)
else:
    plt.show()
