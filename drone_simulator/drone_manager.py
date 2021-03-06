import random
import time
import math
from scipy.spatial.transform import Rotation as R

from drone import Drone
from formations.formation_ui_element import loadFormationSelectionFrame

import cflib.crtp

from panda3d.core import Vec3
from direct.showbase import DirectObject
from direct.gui.DirectGui import DirectButton
from direct.gui.DirectGui import DirectEntry
from direct.gui.DirectGui import DirectFrame


class DroneManager(DirectObject.DirectObject):

    def __init__(self, base, droneList, delay):
        self.base = base
        # the actual dimensions of the bcs drone lab in meters
        # self.roomSize = Vec3(3.40, 4.56, 2.56)
        # confined dimensions because the room and drone coordinates dont match up yet.
        # Also, flying near the windows/close to walls/too high often makes the llighthouse positioning system loose track
        self.roomSize = Vec3(1.5, 2.5, 1.7)
        self.initDrones(droneList)
        self.initUI()

        self.currentFormation = 0
        self.isRotating = False

        self.currentTimeslot = 0

        self.timeslotLengthMilli = delay


    def initDrones(self, droneList):
        """Initializes the drones defined in droneList."""
        self.isStarted = False
        self.isConnected = False
        self.drones = []  # this is the list of all drones
        self.currentDronePos = []  # this is the list of the most recent position that was sent by each drone

        if droneList == []:
            print("No drones to spawn")
        else:
            for i in range(0, len(droneList)):
                position = droneList[i][0]
                uri = droneList[i][1]
                self.drones.append(Drone(self, position, uri=uri))

        self.base.taskMgr.add(self.updateDronesTask, "UpdateDrones")
        self.base.taskMgr.add(self.updateTimeslotTask, "UpdateTimeslot")

    def updateDronesTask(self, task):
        """Run the update methods of all drones."""
        for drone in self.drones:
            drone.update()
        return task.cont

    def updateTimeslotTask(self, task):
        timeslotAmount = 2
        task.delayTime = self.timeslotLengthMilli / 1000

        self.currentTimeslot += 1
        if self.currentTimeslot >= timeslotAmount:
            self.currentTimeslot = 0

        for drone in self.drones:
            drone.updateSentPosition(self.currentTimeslot)

        return task.again

    def initUI(self):
        # initialize drone control panel
        buttonSize = (-4, 4, -.2, .8)
        buttonDistance = 0.15
    
        entrySize = (0, 2, -.2, .8)

        # frame = DirectFrame(frameColor=(.2, .2, .2, 1), frameSize=(-.5, .5, -.7, .15), pos=(-.9, 0, -.6), scale=.5)
        frame = DirectFrame(frameColor=(.2, .2, .2, 1), frameSize=(-.5, .5, -.7, .15), pos=(-.9, 0, -.4), scale=.5)

        button = DirectButton(text="Start", scale=.1, frameSize=buttonSize, command=self.startLandAll)
        button["extraArgs"] = [button]
        button.reparentTo(frame)

        button = DirectButton(text="Random Target", scale=.1, frameSize=buttonSize, command=self.setRandomTargets)
        button.reparentTo(frame)
        button.setPos(Vec3(0, 0, -1 * buttonDistance))

        button = DirectButton(text="Stop", scale=.1, frameSize=buttonSize, command=self.stopAll)
        button.reparentTo(frame)
        button.setPos(Vec3(0, 0, -2 * buttonDistance))

        button = DirectButton(text="Return", scale=.1, frameSize=buttonSize, command=self.returnToWaitingPosition)
        button.reparentTo(frame)
        button.setPos(Vec3(0, 0, -3 * buttonDistance))

        button = DirectButton(text="Connect", scale=.1, frameSize=buttonSize, command=self.toggleConnections)
        button["extraArgs"] = [button]
        button.reparentTo(frame)
        button.setPos(Vec3(0, 0, -4 * buttonDistance))

        button = DirectButton(text="Rotate", scale=.1, frameSize=buttonSize, command=self.toggleRotation)
        button.reparentTo(frame)
        button.setPos(Vec3(0, 0, -5 * buttonDistance))

        button = DirectButton(text="Move", scale=.1, frameSize=buttonSize, command=self.moveFormation)
        button.reparentTo(frame)
        button.setPos(Vec3(0, 0, -6 * buttonDistance))

        self.moveX = DirectEntry(text="", initialText="0", scale=.1, frameSize=entrySize)
        self.moveX.reparentTo(frame)
        self.moveX.setPos(Vec3(0.5, 0, -6 * buttonDistance))

        self.moveY = DirectEntry(text="", initialText="0", scale=.1, frameSize=entrySize)
        self.moveY.reparentTo(frame)
        self.moveY.setPos(Vec3(0.75, 0, -6 * buttonDistance))

        self.moveZ = DirectEntry(text="", initialText="0", scale=.1, frameSize=entrySize)
        self.moveZ.reparentTo(frame)
        self.moveZ.setPos(Vec3(1, 0, -6 * buttonDistance))

        self.rotSpeed = DirectEntry(text="", initialText="3", scale=.1, frameSize=entrySize)
        self.rotSpeed.reparentTo(frame)
        self.rotSpeed.setPos(Vec3(0.5, 0, -5 * buttonDistance))

        # initialize an UI element with all available formations
        loadFormationSelectionFrame(self)


    def startLandAll(self, button):
        if not self.isStarted:
            self.isStarted = True
            button["text"] = "Land"
            print("starting all")
            for drone in self.drones:
                pos = drone.getPos()
                drone.setTarget(target=Vec3(pos[0], pos[1], 1))
        else:
            self.isStarted = False
            button["text"] = "Start"
            print("landing all")
            for drone in self.drones:
                pos = drone.getPos()
                drone.setTarget(target=Vec3(pos[0], pos[1], 0))


    def returnToWaitingPosition(self):
        """Makes all drones hover above their starting position. Useful to make the drones land just where they started."""
        if not self.isStarted:
            print("can't return to waiting position, drones are not started")
            return
        print("returning to waiting positions")
        for drone in self.drones:
            drone.setTarget(drone.waitingPosition)


    def setRandomTargets(self):
        """Set random targets for all drones."""
        if not self.isStarted:
            print("can't set random targets, drones are not started")
            return
        print("setting random targets")
        for drone in self.drones:
            drone.setRandomTarget()


    def stopAll(self):
        """Stops all drones and makes them hover where they are."""
        if not self.isStarted:
            print("can't stop drones, drones are not started")
            return
        print("stopping drones")
        for drone in self.drones:
            drone.setTarget(target=drone.getPos())


    def toggleConnections(self, button):
        """Connects/Disconnects the virtual drones to/from the real drones."""
        # connect drones
        if not self.isConnected:
            self.isConnected = True
            button["text"] = "Disconnect"
            print("initializing drivers")
            cflib.crtp.init_drivers(enable_debug_driver=False)
            print("connecting drones")
            for drone in self.drones:
                drone.connect()
            # time.sleep(5)  # wait a moment so that the position estimator reports a consisten position
        # disconnect drones
        else:
            self.isConnected = False
            button["text"] = "Connect"
            print("disconnecting drones")
            for drone in self.drones:
                if drone.isConnected:
                    drone.disconnect()


    def applyFormation(self, formation):
        """Applies the supplied formation to the drones."""
        if not self.isStarted:
            print("Can't apply formation, drones are not started")
            return

        # name = formation[0]
        dronePositions = formation[1]
        requiredDrones = len(dronePositions)

        availableDrones = self.drones.__len__()
        maxNumber = availableDrones
        if requiredDrones > availableDrones:
            print("The formation contains {0} points but there are only {1} available drones".format(requiredDrones, availableDrones))

        if requiredDrones < availableDrones:
            print("The formation contains {0} points but there are {1} available drones, some drones will remain stationary".format(requiredDrones, availableDrones))
            maxNumber = requiredDrones

        # print("applying {} formation".format(formation[0]))
        for i in range(0, maxNumber):
            self.drones[i].setNewRandVec()
            self.drones[i].setTarget(Vec3(dronePositions[i, 0], dronePositions[i, 1], dronePositions[i, 2]))

        self.currentFormation = formation


    def moveFormation(self):
        if(self.currentFormation == 0):
            return
        newFormation = self.currentFormation
        newFormation[1] += [float(self.moveX.get()), float(self.moveY.get()), float(self.moveZ.get())]
        self.applyFormation(newFormation)


    def toggleRotation(self):
        if(self.currentFormation == 0):
            return
        if not self.isRotating:
            self.isRotating = True
            self.base.taskMgr.doMethodLater(0, self.rotateFormationTask, "RotateDrones")
        else:
            self.isRotating = False
            self.base.taskMgr.remove("RotateDrones")


    def rotateFormationTask(self, task):
        task.delayTime = 0.1
        newFormation = self.currentFormation
        speed = 2
        try:
            speed = float(self.rotSpeed.get())
        except:
            speed = 2
        r = R.from_euler('xyz', [0, 0, speed], degrees=True)
        newFormation[1] = r.apply(newFormation[1])
        self.applyFormation(newFormation)
        return task.again

    def getRandomRoomCoordinate(self) -> Vec3:
        """Returns random 3D coordinates withing the confines of the room."""
        newX = random.uniform(-self.roomSize.x / 2, self.roomSize.x / 2)
        newY = random.uniform(-self.roomSize.y / 2, self.roomSize.y / 2)
        newZ = random.uniform(0 + 0.3, self.roomSize.z)
        return Vec3(newX, newY, newZ)


    def getAllPositions(self):
        """Returns a list of the positions of all drones. Usefull when recording their paths for later."""
        lst = []
        for drone in self.drones:
            pos = drone.getPos()
            lst.append([pos.x, pos.y, pos.z])
        return lst

    def getAllVelocities(self):
        """Returns a list of the velocities of all drones. Usefull when recording their paths for later."""
        lst = []
        for drone in self.drones:
            vel = drone.getVel()
            lst.append([vel.x, vel.y, vel.z])
        return lst
