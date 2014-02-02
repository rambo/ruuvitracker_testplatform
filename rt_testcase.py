#!/usr/bin/env python
"""Baseclass for RuuviTracker testcases, since we need DBUS we will use glib mainloop as our eventloop"""
import sys,os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from exceptions import NotImplementedError
from scpi.devices import hp6632b
from dbushelpers.call_cached import call_cached as dbus_call_cached
import time, datetime
import signal
import io
import csv

class rt_testcase(object):
    def __init__(self, *args, **kwargs):
        super(rt_testcase, self).__init__(*args, **kwargs)
        self.loop = gobject.MainLoop()
        self.bus = dbus.SessionBus()
        self.hp6632b = hp6632b.rs232('/dev/ttyUSB0')
        self.arduino_path = "/fi/hacklab/ardubus/ruuvitracker_tester"
        # Currently our only input is the pulse so the method name is apt even though we trap all alias signals (also dio_change:s)
        self.bus.add_signal_receiver(self.pulse_received, dbus_interface = "fi.hacklab.ardubus", signal_name = "alias_change", path=self.arduino_path)
        self.pulse_trains = []
        self._active_pulse_train = False
        self.logger = None

        # Finish by restoring a known state
        self.set_defaut_state()

    def set_defaut_state(self):
        """Reset everything back to known states"""
        self.enable_usb(False)
        self.hp6632b.reset()
        self.hp6632b.set_remote_mode() # Enter remote mode, so stray finger do not immediately ruin things for us
        self.hp6632b.set_output(False) # reset above actuall should do this, but make sure..
        self.hp6632b.set_voltage(4100) # output is disabled, this is just default for us when we enable output
        self.hp6632b.set_current(50) # 50mA should be safe enough
        self.reset_stm32() # Everything is powered down but this will set the relevant pins to known state
        # Set the board upright and facing "forward"
        self.set_pan(10)
        self.set_tilt(62)
        time.sleep(0.700) # Give the servos time to actually move to position
        self.enable_servos(False) # The servos *will* jitter, in some angles more than others, disabling them prevents this
        self.pulse_trains = []
        self._active_pulse_train = False

    def power_down(self):
        """Cuts power from the module, both USB and hp6632b"""
        self.enable_usb(False)
        self.hp6632b.set_output(False)

    def power_up(self):
        """Shorthand for enabling output on the hp6632b"""
        self.hp6632b.set_output(True)

    def set_power(self, millivolts, milliamps):
        """Sets the "battery" to given voltage + current AND enables output on the hp6632b"""
        self.hp6632b.set_voltage(millivolts)
        self.hp6632b.set_current(milliamps)
        self.hp6632b.set_output(True)

    def set_pan(self, angle):
        """Enables servo power and sets target angle for the pan-servo, you are responsible for disabling servo power later"""
        self.enable_servos()
        dbus_call_cached(self.arduino_path, 'set_alias', 'pan', angle)

    def set_tilt(self, angle):
        """Enables servo power and sets target angle for the tilt-servo, you are responsible for disabling servo power later"""
        self.enable_servos()
        dbus_call_cached(self.arduino_path, 'set_alias', 'tilt', angle)

    # TODO: methods to do variable speed pan & tilt from a to b

    def enable_servos(self, state=True):
        """Enables servo DC power, or disables if state is set to False"""
        dbus_call_cached(self.arduino_path, 'set_alias', 'servo_power', state)

    def enable_usb(self, state=True):
        """Enables power to the USB hub, or disables if state is set to False"""
        dbus_call_cached(self.arduino_path, 'set_alias', 'usb_power', state)

    def reset_stm32(self, enter_bootloader=False):
        """Boots the STM32 on the board, optionally will enter bootloader mode (though only if the board is actually powered on at this point...)"""
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

    def get_bootloader(self):
        """Shorthand for rebooting the STM32 to bootloader and cycling USB"""
        self.enable_usb(False)
        self.reset_stm32(True)
        # Give the controller time to wake up
        time.sleep(0.100)
        self.enable_usb(True)
        # TODO: Make sure the bootloader actually shows up on device tree

    def get_serialport(self):
        """Shorthand for rebooting the STM32 and cycling USB"""
        self.enable_usb(False)
        self.reset_stm32()
        # Give the controller time to wake up
        time.sleep(0.100)
        self.enable_usb(True)
        # TODO: Make sure the serialport actually shows up on device tree
        # TODO: Find out which /dev/ttyACM it got bound to and return that as string

    def pulse_received(self, alias, usec, sender):
        """This callback handles counting of the pulse-trains from pb0"""
        print " *** got %d from '%s' *** " % (usec, alias)
        if alias != 'rt_pb0': # in we get signals from other aliases...
            return

        if (    usec > 4000
            and not self._active_pulse_train):
            # new train
            self.pulse_trains.append([])
            self._active_pulse_train = True
            return

        if (    usec > 4000
            and self._active_pulse_train):
            # end of train
            self._active_pulse_train = False
            self.sync_received(len(self.pulse_trains[-1]))
            return

        # For shorter values append to the sync train
        self.pulse_trains[-1].append(usec)

    def sync_received(self, short_pulse_count):
        """Callback, you should override this to handle the syncs your tests need (but call this if you want the sync logged)"""
        self.log_data('','',short_pulse_count) # Do not waste time measuring voltage or current
        pass

    def open_logfile(self, suffix=None):
        if not suffix:
            suffix = os.path.basename(__file__) # TODO: better automagic ?
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs', "%s_%s" % (time.strftime("%Y-%m-%d_%H%M"), suffix))
        # Open buffered file stream
        self.log_handle = io.open(filename, mode='wb')
        # Make it CSV
        self.logger = csv.writer(self.log_handle)
        # And write the header
        self.logger.writerow([u'Time',u'Voltage', u'Current', u'Syncpulses'])

    def log_data(self, *args):
        if not self.logger:
            self.open_logfile()
        row = [ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") ] + list(args)
        self.logger.writerow(row)

    def log_voltage_et_current(self):
        self.log_data(self.hp6632b.measure_voltage(), self.hp6632b.measure_current(), '')

    # TODO: add methods for copying the testcase lua files to romfs (testcase.lua -> autorun.lua)
    
    # TODO: add helper for recompiling
    
    # TODO: add helper for flashing

    def hook_signals(self):
        """Hooks common UNIX signals to corresponding handlers"""
        signal.signal(signal.SIGTERM, self.quit)
        signal.signal(signal.SIGQUIT, self.quit)
        signal.signal(signal.SIGHUP, self.set_defaut_state)

    def run(self):
        """The actual test, must call run_eventloop and must be event-oriented for timing long-running events"""
        raise NotImplementedError()

    def run_eventloop(self):
        self.loop.run()

    def quit(self):
        self.log_handle.close()
        self.hp6632b.quit()
        self.loop.quit()

