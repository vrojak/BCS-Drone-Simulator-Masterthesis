import time
import math
import random

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

from panda3d.core import Vec3
from panda3d.core import BitMask32
from panda3d.core import LineSegs
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletGhostNode


class Drone:

    # RIGIDBODYMASS = 1
    # RIGIDBODYRADIUS = 0.1
    # LINEARDAMPING = 0.97
    # SENSORRANGE = 0.6
    # TARGETFORCE = 3
    # AVOIDANCEFORCE = 25
    # FORCEFALLOFFDISTANCE = .5

    RIGIDBODYMASS = 0.5
    RIGIDBODYRADIUS = 0.1
    LINEARDAMPING = 0.95
    SENSORRANGE = 0.6
    TARGETFORCE = 1
    AVOIDANCEFORCE = 10
    FORCEFALLOFFDISTANCE = .5

    def __init__(self, manager, position: Vec3, uri="-1", printDebugInfo=False):

        self.base = manager.base
        self.manager = manager

        # The position of the real drone this virtual drone is connected to.
        # If a connection is active, this value is updated each frame.
        self.realDronePosition = Vec3(0, 0, 0)

        self.canConnect = False  # true if the virtual drone has a uri to connect to a real drone
        self.isConnected = False  # true if the connection to a real drone is currently active
        self.uri = uri
        if self.uri != "-1":
            self.canConnect = True
        self.id = int(uri[-1])

        self.randVec = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))

        # add the rigidbody to the drone, which has a mass and linear damping
        self.rigidBody = BulletRigidBodyNode("RigidSphere")  # derived from PandaNode
        self.rigidBody.setMass(self.RIGIDBODYMASS)  # body is now dynamic
        self.rigidBody.addShape(BulletSphereShape(self.RIGIDBODYRADIUS))
        self.rigidBody.setLinearSleepThreshold(0)
        self.rigidBody.setFriction(0)
        self.rigidBody.setLinearDamping(self.LINEARDAMPING)
        self.rigidBodyNP = self.base.render.attachNewNode(self.rigidBody)
        self.rigidBodyNP.setPos(position)
        # self.rigidBodyNP.setCollideMask(BitMask32.bit(1))
        self.base.world.attach(self.rigidBody)

        # add a 3d model to the drone to be able to see it in the 3d scene
        model = self.base.loader.loadModel(self.base.modelDir + "/drones/drone1.egg")
        model.setScale(0.2)
        model.reparentTo(self.rigidBodyNP)

        self.target = position  # the long term target that the virtual drones tries to reach
        self.setpoint = position  # the immediate target (setpoint) that the real drone tries to reach, usually updated each frame
        self.waitingPosition = Vec3(position[0], position[1], 0.7)
        self.lastSentPosition = self.waitingPosition  # the position that this drone last sent around

        self.printDebugInfo = printDebugInfo
        if self.printDebugInfo:  # put a second drone model on top of drone that outputs debug stuff
            model = self.base.loader.loadModel(self.base.modelDir + "/drones/drone1.egg")
            model.setScale(0.4)
            model.setPos(0, 0, .2)
            model.reparentTo(self.rigidBodyNP)

        # initialize line renderers
        self.targetLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.velocityLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.forceLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.actualDroneLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.setpointNP = self.base.render.attachNewNode(LineSegs().create())


    def connect(self):
        """Connects the virtual drone to a real one with the uri supplied at initialization."""
        if not self.canConnect:
            return
        print(self.uri, "connecting")
        self.isConnected = True
        self.scf = SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache'))
        self.scf.open_link()
        self._reset_estimator()
        self.start_position_printing()

        # MOVE THIS BACK TO SENDPOSITIONS() IF STUFF BREAKS
        self.scf.cf.param.set_value('flightmode.posSet', '1')


    def sendPosition(self):
        """Sends the position of the virtual drone to the real one."""
        cf = self.scf.cf
        self.setpoint = self.getPos()
        # send the setpoint
        cf.commander.send_position_setpoint(self.setpoint[0], self.setpoint[1], self.setpoint[2], 0)


    def disconnect(self):
        """Disconnects the real drone."""
        print(self.uri, "disconnecting")
        self.isConnected = False
        cf = self.scf.cf
        cf.commander.send_stop_setpoint()
        time.sleep(0.1)
        self.scf.close_link()


    def update(self):
        """Update the virtual drone."""
        # self.updateSentPositionBypass(0)

        self._updateTargetForce()
        self._updateAvoidanceForce()
        self._clampForce()

        if self.isConnected:
            self.sendPosition()

        # draw various lines to get a better idea of whats happening
        self._drawTargetLine()
        # self._drawVelocityLine()
        self._drawForceLine()
        # self._drawSetpointLine()

        self._printDebugInfo()
    
    def updateSentPosition(self, timeslot):
        transmissionProbability = 1
        if self.id == timeslot:
            if random.uniform(0, 1) < transmissionProbability:
                # print(f"drone {self.id} updated position")
                self.lastSentPosition = self.getPos()
            else:
                pass
                # print(f"drone {self.id} failed!")

    def updateSentPositionBypass(self, timeslot):
        self.lastSentPosition = self.getPos()

    def getPos(self) -> Vec3:
        return self.rigidBodyNP.getPos()

    
    def getLastSentPos(self) -> Vec3:
        return self.lastSentPosition


    def _updateTargetForce(self):
        """Applies a force to the virtual drone which moves it closer to its target."""
        dist = (self.target - self.getPos())
        if(dist.length() > self.FORCEFALLOFFDISTANCE):
            force = dist.normalized()
        else:
            force = (dist / self.FORCEFALLOFFDISTANCE)
        self.addForce(force * self.TARGETFORCE)


    def _updateAvoidanceForce(self):
        """Applies a force the the virtual drone which makes it avoid other drones."""
        # get all drones within the sensors reach and put them in a list
        nearbyDrones = []
        for drone in self.manager.drones:
            dist = (drone.getLastSentPos() - self.getPos()).length()
            if drone.id == self.id:  # prevent drone from detecting itself
                continue
            if dist < self.SENSORRANGE: 
                nearbyDrones.append(drone)

        # calculate and apply forces
        for nearbyDrone in nearbyDrones:
            distVec = nearbyDrone.getLastSentPos() - self.getPos()
            if distVec.length() < 0.2:
                print("BONK")
            distMult = self.SENSORRANGE - distVec.length()
            avoidanceDirection = self.randVec.normalized() * 2 - distVec.normalized() * 10
            avoidanceDirection.normalize()
            self.addForce(avoidanceDirection * distMult * self.AVOIDANCEFORCE)


    def _clampForce(self):
        """Clamps the total force acting in the drone."""
        totalForce = self.rigidBody.getTotalForce()
        if totalForce.length() > 2:
            self.rigidBody.clearForces()
            self.rigidBody.applyCentralForce(totalForce.normalized())


    def targetVector(self) -> Vec3:
        """Returns the vector from the drone to its target."""
        return self.target - self.getPos()


    def _printDebugInfo(self):
        if self.printDebugInfo:
            pass


    def setTarget(self, target: Vec3):
        """Sets a new target for the drone."""
        self.target = target


    def setRandomTarget(self):
        """Sets a new random target for the drone."""
        self.target = self.manager.getRandomRoomCoordinate()

    
    def setNewRandVec(self):
        self.randVec = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))


    def addForce(self, force: Vec3):
        self.rigidBody.applyCentralForce(force)


    def setPos(self, position: Vec3):
        self.rigidBodyNP.setPos(position)


    def getVel(self) -> Vec3:
        return self.rigidBody.getLinearVelocity()


    def setVel(self, velocity: Vec3):
        return self.rigidBody.setLinearVelocity(velocity)


    def _drawTargetLine(self):
        self.targetLineNP.removeNode()
        ls = LineSegs()
        # ls.setThickness(1)
        ls.setColor(1.0, 0.0, 0.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.target)
        node = ls.create()
        self.targetLineNP = self.base.render.attachNewNode(node)


    def _drawVelocityLine(self):
        self.velocityLineNP.removeNode()
        ls = LineSegs()
        # ls.setThickness(1)
        ls.setColor(0.0, 0.0, 1.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.getPos() + self.getVel())
        node = ls.create()
        self.velocityLineNP = self.base.render.attachNewNode(node)


    def _drawForceLine(self):
        self.forceLineNP.removeNode()
        ls = LineSegs()
        # ls.setThickness(1)
        ls.setColor(0.0, 1.0, 0.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.getPos() + self.rigidBody.getTotalForce() * 0.2)
        node = ls.create()
        self.forceLineNP = self.base.render.attachNewNode(node)


    def _drawSetpointLine(self):
        self.setpointNP.removeNode()
        ls = LineSegs()
        # ls.setThickness(1)
        ls.setColor(1.0, 1.0, 1.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.setpoint)
        node = ls.create()
        self.setpointNP = self.base.render.attachNewNode(node)


    def _wait_for_position_estimator(self):
        """Waits until the position estimator reports a consistent location after resetting."""
        print('Waiting for estimator to find position...')

        log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
        log_config.add_variable('kalman.varPX', 'float')
        log_config.add_variable('kalman.varPY', 'float')
        log_config.add_variable('kalman.varPZ', 'float')

        var_y_history = [1000] * 10
        var_x_history = [1000] * 10
        var_z_history = [1000] * 10

        threshold = 0.001

        with SyncLogger(self.scf, log_config) as logger:
            for log_entry in logger:
                data = log_entry[1]

                var_x_history.append(data['kalman.varPX'])
                var_x_history.pop(0)
                var_y_history.append(data['kalman.varPY'])
                var_y_history.pop(0)
                var_z_history.append(data['kalman.varPZ'])
                var_z_history.pop(0)

                min_x = min(var_x_history)
                max_x = max(var_x_history)
                min_y = min(var_y_history)
                max_y = max(var_y_history)
                min_z = min(var_z_history)
                max_z = max(var_z_history)

                if (max_x - min_x) < threshold and (
                        max_y - min_y) < threshold and (
                        max_z - min_z) < threshold:
                    break


    def _reset_estimator(self):
        """Resets the position estimator, this should be run before flying the drones or they might report a wrong position."""
        cf = self.scf.cf
        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')

        self._wait_for_position_estimator()


    def position_callback(self, timestamp, data, logconf):
        """Updates the variable holding the position of the actual drone. It is not called in the update method, but by the drone itself (I think)."""
        x = data['kalman.stateX']
        y = data['kalman.stateY']
        z = data['kalman.stateZ']
        self.realDronePosition = Vec3(x, y, z)
        # print('pos: ({}, {}, {})'.format(x, y, z))


    def start_position_printing(self):
        """Activate logging of the position of the real drone."""
        log_conf = LogConfig(name='Position', period_in_ms=50)
        log_conf.add_variable('kalman.stateX', 'float')
        log_conf.add_variable('kalman.stateY', 'float')
        log_conf.add_variable('kalman.stateZ', 'float')

        self.scf.cf.log.add_config(log_conf)
        log_conf.data_received_cb.add_callback(self.position_callback)
        log_conf.start()
