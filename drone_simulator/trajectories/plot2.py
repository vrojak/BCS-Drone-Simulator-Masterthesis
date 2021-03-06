import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider  # , Button, RadioButtons
from mpl_toolkits.mplot3d import Axes3D

amount = 4
delay = 120
run = 6
traj = np.load(sys.path[0] + f"/{amount}quads/{delay}/pos_traj_{run}.npy")
vel = np.load(sys.path[0] + "/4quads/0/vel_traj_6.npy")
agents = traj.shape[0]
timesteps = traj.shape[1]

print(f"Showing {traj.shape[2]}D trajectories of {agents} agents with {timesteps} timesteps")

fig = plt.figure()
# fig = plt.figure(figsize=(4, 35))
fig.subplots_adjust(bottom=.25, top=.75)
ax = fig.add_subplot(111, projection='3d')
# fig.subplots_adjust()


plotRange = 1

ax.set_xlim3d(-plotRange, plotRange)
ax.set_ylim3d(-plotRange, plotRange)
# ax.set_zlim3d(0, 2 * plotRange)
ax.set_zlim3d(.5, 1.5)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')

ax.view_init(elev=32, azim=35)
fig.set_size_inches(10, 10)

# Turn off tick labels
# ax.set_xticklabels([])
# ax.set_yticklabels([])
# ax.set_zticklabels([])

step = timesteps - 1
for i in range(0, agents):
    trail = max(0, step - 999999)
    ax.plot3D(traj[i, trail:step + 1, 0], traj[i, trail:step + 1, 1], traj[i, trail:step + 1, 2])
    ax.scatter(traj[i, step, 0], traj[i, step, 1], traj[i, step, 2])

SAVE = True
if SAVE:
    plt.savefig(sys.path[0] + f"/{amount}q{delay}.pdf", dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches='tight', pad_inches=.1,
                frameon=None, metadata=None)
else:
    plt.show()


################ calculations for metrics ################
# deltaTime = 0.0508
# startPoints = np.around(traj[:,0,:], 0)
# endPoints = np.around(traj[:,-1,:], 2)

# ### COMPLETION TIME ###
# diff = np.zeros((agents, timesteps, 3))
# for t in range(0, timesteps):
#     diff[:, t, :] = traj[:, t, :] - endPoints
# diff = np.square(diff)
# diff = np.sum(diff, axis=2)
# diff = np.sqrt(diff)

# completionTime = 0
# completionTime = "DNF"
# completionMargin = 0.03
# for t in range(0, timesteps):
#     # print(f"{t}:")
#     # print(diff[:,t])
#     finished = True
#     for ag in range(0, agents):
#         if diff[ag,t] > completionMargin:
#             finished = False
#     if finished:
#         completionStep = t
#         completionTime = completionStep * deltaTime
#         break

# ### TOTAL DISTANCE ###
# def distanceBetweenSteps(arr, t):
#     diff = arr[:,t,:] - arr[:,t+1,:]
#     diff = np.square(diff)
#     diff = np.sum(diff, axis=1)
#     diff = np.sqrt(diff)
#     diff = np.sum(diff, axis=0)
#     return diff

# totalDistance = 0
# for t in range(0, completionStep-1):
#     totalDistance += distanceBetweenSteps(traj, t)

# beelineDistance = startPoints - endPoints
# beelineDistance = np.square(beelineDistance)
# beelineDistance = np.sum(beelineDistance, axis=1)
# beelineDistance = np.sqrt(beelineDistance)
# beelineDistance = np.sum(beelineDistance, axis=0)
    
# ### CLOSEST APPROACH ###
# def distanceBetweenDrones(arr, t, ag1, ag2):
#     dist = arr[ag1,t,:] - arr[ag2,t,:]
#     dist = np.square(dist)
#     dist = np.sum(dist)
#     dist = np.sqrt(dist)
#     return dist

# closestApproach = 99999999
# closestApproachTimestep = -1
# for t in range(0, timesteps):
#     for ag1 in range(0, agents):
#         for ag2 in range(ag1+1, agents):
#             dist = distanceBetweenDrones(traj, t, ag1, ag2)
#             if dist < closestApproach:
#                 closestApproach = dist
#                 closestApproachTimestep = t

# ### LARGEST ACCELERATION ###
# def getDiffs(arr):
#     diffArr = np.zeros((agents, arr.shape[1]-1, 3))
#     for t in range(0, arr.shape[1]-1):
#         diffArr[:,t,:] = arr[:,t,:] - arr[:,t+1,:]
#     diffArr /= deltaTime
#     return diffArr

# def getAcc(arr):
#     diffArr = np.zeros((agents, timesteps-2, 3))
#     for t in range(0, timesteps-2):
#         diffArr[:,t,:] = arr[:,t,:] - 2 * arr[:,t+1,:] + arr[:,t+2,:]
#     diffArr /= (deltaTime * deltaTime)
#     return diffArr

# # vel = getDiffs(traj)
# # acc = getDiffs(vel)
# acc = getAcc(traj)
# acc = np.square(acc)
# acc = np.sum(acc, axis=2)
# acc = np.sqrt(acc)

# accMax = 0
# accMaxTimestep = 0
# for t in range(0, timesteps-2):
#     for ag in range(0, agents):
#         if acc[ag,t] > accMax:
#             accMax = acc[ag,t]
#             accMaxTimestep = t

# acc3 = getDiffs(vel)
# acc3 = np.square(acc3)
# acc3 = np.sum(acc3, axis=2)
# acc3 = np.sqrt(acc3)
# acc3Max = 0
# acc3MaxTimestep = 0
# for t in range(0, timesteps-2):
#     for ag in range(0, agents):
#         if acc3[ag,t] > acc3Max:
#             acc3Max = acc3[ag,t]
#             acc3MaxTimestep = t

# print("##############")
# print("START POINTS")
# print(startPoints)
# print("END POINTS")
# print(endPoints)
# print(f"Completion time: {completionTime}s @ timestep {completionStep}")
# print(f"Total distance: {totalDistance}, beeline distance: {beelineDistance}, efficiency: {beelineDistance / totalDistance}")
# print(f"Closest approach: {closestApproach} @ timestep {closestApproachTimestep}")
# print(f"Largest Acceleration: {accMax} @ timestep {accMaxTimestep}")
# print(f"Debug: {acc3Max} {acc3MaxTimestep} vel")
