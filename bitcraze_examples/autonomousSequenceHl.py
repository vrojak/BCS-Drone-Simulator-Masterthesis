# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2018 Bitcraze AB
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
"""
This script shows the basic use of the PositionHlCommander class.

Simple example that connects to the crazyflie at `URI` and runs a
sequence. This script requires some kind of location system.

The PositionHlCommander uses position setpoints.

Change the URI variable to your Crazyflie configuration.
"""

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander

import time
from transformation import CoordTransform

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E1'


def position_callback(timestamp, data, logconf):
    x = data['kalman.stateX']
    y = data['kalman.stateY']
    z = data['kalman.stateZ']
    print('pos: ({}, {}, {})'.format(x, y, z))


def start_position_printing(scf):
    log_conf = LogConfig(name='Position', period_in_ms=500)
    log_conf.add_variable('kalman.stateX', 'float')
    log_conf.add_variable('kalman.stateY', 'float')
    log_conf.add_variable('kalman.stateZ', 'float')

    scf.cf.log.add_config(log_conf)
    log_conf.data_received_cb.add_callback(position_callback)
    log_conf.start()


def slightly_more_complex_usage():
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        with PositionHlCommander(
                scf,
                x=0.0, y=0.0, z=0.0,
                default_velocity=0.3,
                default_height=0.5,
                controller=PositionHlCommander.CONTROLLER_MELLINGER) as pc:
            # Go to a coordinate
            pc.go_to(1.0, 1.0, 1.0)

            # Move relative to the current position
            pc.right(1.0)

            # Go to a coordinate and use default height
            pc.go_to(0.0, 0.0)

            # Go slowly to a coordinate
            pc.go_to(1.0, 1.0, velocity=0.2)

            # Set new default velocity and height
            pc.set_default_velocity(0.3)
            pc.set_default_height(1.0)
            pc.go_to(0.0, 0.0)


def simple_sequence():
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        with PositionHlCommander(scf) as pc:
            pc.forward(1.0)
            pc.left(1.0)
            pc.back(1.0)
            pc.go_to(0.0, 0.0, 1.0)


def rectangle_sequence():
    tfm = CoordTransform()
    center_floor = tfm.transformF2F(0.5, 0.5, 0)

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        with PositionHlCommander(
                scf,
                x=center_floor[0], y=center_floor[1], z=center_floor[2],
                default_velocity=0.3,
                default_height=0.5,
                controller=PositionHlCommander.CONTROLLER_MELLINGER) as pc:
            fastSpeed = .5 # not more than 1.4!
            pc.go_to(*tfm.transformF2F(0.5, 0.5, 1))
            pc.go_to(*tfm.transformF2F(0, 0, 1), fastSpeed)
            pc.go_to(*tfm.transformF2F(1, 0, 1), fastSpeed)
            pc.go_to(*tfm.transformF2F(1, 1, 1), fastSpeed)
            pc.go_to(*tfm.transformF2F(0, 1, 1), fastSpeed)
            pc.go_to(*tfm.transformF2F(0, 0, 1), fastSpeed)
            pc.go_to(*tfm.transformF2F(0.5, 0.5, 1), fastSpeed)
            pc.go_to(*tfm.transformF2F(0.5, 0.5, 0))   


def square():
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                with PositionHlCommander(
                        scf,
                        x=0, y=0, z=0,
                        default_velocity=0.3,
                        default_height=0.2,
                        controller=PositionHlCommander.CONTROLLER_MELLINGER) as pc:
                                print(pc.get_position())
                                pc.up(.5)
                                print(pc.get_position())
                                pc.right(.5)
                                print(pc.get_position())
                                pc.forward(.5)
                                print(pc.get_position())
                                pc.left(1)
                                print(pc.get_position())
                                pc.back(1)
                                print(pc.get_position())
                                pc.right(1)
                                print(pc.get_position())
                                pc.forward(.5)
                                print(pc.get_position())
                                pc.left(.5)
                                print(pc.get_position())
                                pc.down(.5)
                                print(pc.get_position())


def double_square():
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                with PositionHlCommander(
                        scf,
                        x=0, y=0, z=0,
                        default_velocity=0.5,
                        default_height=0.2,
                        controller=PositionHlCommander.CONTROLLER_MELLINGER) as pc:
                                size = .8
                                max_height = 1.8
                                pc.go_to(-size,-size,1)
                                pc.go_to(size,-size,1)
                                pc.go_to(size,size,1)
                                pc.go_to(-size,size,1)
                                pc.go_to(-size,-size,1)
                                pc.go_to(-size,-size,max_height)
                                pc.go_to(size,-size,max_height)
                                pc.go_to(size,size,max_height)
                                pc.go_to(-size,size,max_height)
                                pc.go_to(-size,-size,max_height)
                                pc.go_to(0,0,.2)


def room_border():
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                start_position_printing(scf)
                with PositionHlCommander(
                        scf,
                        x=0, y=0, z=0,
                        default_velocity=0.3,
                        default_height=0.2,
                        controller=PositionHlCommander.CONTROLLER_MELLINGER) as pc:
                                height = 1
                                pc.go_to(-1.3,-1.8,height)
                                pc.go_to(1.3,-1.8,height)
                                pc.go_to(1.3,1.8,height)
                                pc.go_to(-1.3,1.8,height)
                                pc.go_to(-1.3,-1.8,height)



def test():
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                with PositionHlCommander(
                        scf,
                        x=0, y=0, z=0,
                        default_velocity=0.3,
                        default_height=0.2,
                        controller=PositionHlCommander.CONTROLLER_MELLINGER) as pc:
                                pc.go_to(-1.3,-1.8,0.3)


if __name__ == '__main__':
        cflib.crtp.init_drivers(enable_debug_driver=False)

        # simple_sequence()
        # slightly_more_complex_usage()
        # rectangle_sequence()
        square()
        # double_square()
        # test()
        #room_border()