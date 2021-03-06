import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider  # , Button, RadioButtons
from mpl_toolkits.mplot3d import Axes3D

amount = 4
delay = 120
run = 10
traj = np.load(sys.path[0] + f"/{amount}quads/{delay}/pos_traj_{run}.npy")
agents = traj.shape[0]
timesteps = traj.shape[1]

print("Showing {2}D trajectories of {0} agents with {1} timesteps".format(traj.shape[0], traj.shape[1], traj.shape[2]))

fig = plt.figure()
# ax = fig.add_subplot(111, aspect='equal', projection='3d')
plt.subplots_adjust(bottom=0.25)  # make room for the slider
ax = fig.add_subplot(111, projection='3d')

ax_step = plt.axes([0.25, 0.1, 0.65, 0.03])
s_step = Slider(ax_step, 'timestep', 0, timesteps - 1, valinit=0, valstep=1)

plotRange = 1


def update(val):
    step = int(s_step.val)
    ax.clear()
    ax.set_xlim3d(-plotRange, plotRange)
    ax.set_ylim3d(-plotRange, plotRange)
    ax.set_zlim3d(0, 2 * plotRange)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    for i in range(0, agents):
        trail = max(0, step - 999999)
        ax.plot3D(traj[i, trail:step + 1, 0], traj[i, trail:step + 1, 1], traj[i, trail:step + 1, 2])
        ax.scatter(traj[i, step, 0], traj[i, step, 1], traj[i, step, 2])
    fig.canvas.draw_idle()


s_step.on_changed(update)

update(1)  # run update once to set axes range
plt.show()
