#!/usr/bin/env python
"""Baseclass for RuuviTracker testcases, since we need DBUS we will use glib mainloop as our eventloop"""

import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
from exceptions import NotImplementedError
from scpi.devices import hp6632b
from dbushelpers.call_cached import call_cached as dbus_call_cached
import time

class rt_testcase(object):
    def __init__(self, *args, **kwargs):
        super(rt_testcase, self).__init__(*args, **kwargs)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.hp6632b = hp6632b.rs232('/dev/ttyUSB0')
        self.arduino_path = "/fi/hacklab/ardubus/ruuvitracker_tester"

        # Finish by restoring a known state
        self.set_defaut_state()

    def set_defaut_state():
        """Reset everything back to known states"""
        self.enable_usb(False)
        self.hp6632b.set_output(False)
        self.hp6632b.set_voltage(4100) # output is disabled, this is just default for us when we enable output
        self.hp6632b.set_current(50)
        self.reset_stm32() # Everything is powered down but this will set the relevant pins to known state
        # Set the board upright
        self.set_pan(90)
        self.set_tilt(60)
        self.enable_servos(False) # The servos *will* jitter, in some angles more than others, disabling them prevents this

    def set_pan(self, angle):
        self.enable_servos()
        dbus_call_cached(self.arduino_path, 'set_alias', 'pan', angle)

    def set_tilt(self, angle):
        self.enable_servos()
        dbus_call_cached(self.arduino_path, 'set_alias', 'tilt', angle)

    # TODO: methods to do slow pan & tilt from a to b

    def enable_servos(self, state=True):
        dbus_call_cached(self.arduino_path, 'set_alias', 'servo_power', state)

    def enable_usb(self, state=True):
        dbus_call_cached(self.arduino_path, 'set_alias', 'usb_power', state)

    def reset_stm32(self, enter_bootloader=False):
        """Boots the STM32 on the board, optionally will enter bootloader mode (though only if the board is actually powered...)"""
        if enter_bootloader:
            dbus_call_cached(self.arduino_path, 'set_alias', 'rt_boot0', True)
        else:
            dbus_call_cached(self.arduino_path, 'set_alias', 'rt_boot0', False)
        dbus_call_cached(self.arduino_path, 'set_alias', 'rt_nrst', False)
        time.sleep(0.100)
        dbus_call_cached(self.arduino_path, 'set_alias', 'rt_nrst', True)
        if enter_bootloader:
            time.sleep(0.100)
            dbus_call_cached(self.arduino_path, 'set_alias', 'rt_boot0', False)


    def run(self):
        """The actual test, must call run_eventloop and must be event-oriented"""
        raise NotImplementedError()

    def run_eventloop(self):
        loop = gobject.MainLoop()
        loop.run()
