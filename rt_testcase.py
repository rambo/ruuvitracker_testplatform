#!/usr/bin/env python
"""Baseclass for RuuviTracker testcases, since we need DBUS we will use glib mainloop as our eventloop"""
import sys,os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from exceptions import NotImplementedError,RuntimeError
from scpi.devices import hp6632b
from dbushelpers.call_cached import call_cached as dbus_call_cached
import time, datetime
import signal
import io
import csv
import subprocess
import timeout_decorator
import pyudev
import shutil


RT_DFU_DEVICEID = '0483:df11'
RT_SERIAL_DEVICEID = '0483:5740'
HP_SERIALPORT_DEVICEID = '067b:2303' # TODO: Make configurable in yaml or something
COMPILE_TIMEOUT = 120  # seconds
FLASH_TIMEOUT = 120 # seconds

class rt_testcase(object):
    def __init__(self, *args, **kwargs):
        super(rt_testcase, self).__init__(*args, **kwargs)
        self.testname = '' # This should be the testcase class


        self.loop = gobject.MainLoop()
        self.bus = dbus.SessionBus()
        self.hp6632b = hp6632b.rs232(self.get_serialport_tty(HP_SERIALPORT_DEVICEID))
        self.usb_device_present_timeout = 10.0
        self.arduino_path = "/fi/hacklab/ardubus/ruuvitracker_tester"
        # Currently our only input is the pulse so the method name is apt even though we trap all alias signals (also dio_change:s)
        self.bus.add_signal_receiver(self.pulse_received, dbus_interface = "fi.hacklab.ardubus", signal_name = "alias_change", path=self.arduino_path)
        self.pulse_trains = []
        self._active_pulse_train = False
        self.logger = None
        self.log_handle = None
        self.voltage_timer = None
        self._tick_count = 0 # How many ticks this test has been running, ticks are seconds
        self._tick_limit = -1 # infinite
        self._tick_timer = None # This will be set later
        self._cleanup_files = []

        # Some defaults 
        self.default_voltage = 4100 # millivolts
        self.default_current = 50 # milliamps
        self.default_pan = 10
        self.default_tilt = 62
        # note if you change these in setup() make sure theyre suitable
        self.bootloader_voltage = 4100 # millivolts
        self.bootloader_current = 50 # milliamps

        # Testcase should define their defaults here
        self.defaults_setup()
        # Finish by restoring a known state
        self.set_defaut_state()

    def set_defaut_state(self):
        """Reset everything back to known states"""
        self.enable_usb(False)
        self.hp6632b.reset()
        self.hp6632b.set_remote_mode() # Enter remote mode, so stray finger do not immediately ruin things for us
        self.hp6632b.set_output(False) # reset above actuall should do this, but make sure..
        self.hp6632b.set_voltage(self.default_voltage) # output is disabled, this is just default for us when we enable output
        self.hp6632b.set_current(self.default_current) # 50mA should be safe enough
        self.reset_stm32() # Everything is powered down but this will set the relevant pins to known state
        # Set the board upright and facing "forward"
        self.set_pan(self.default_pan)
        self.set_tilt(self.default_tilt)
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

    def hold_stm32_reset(self):
        """Holds the reset line down"""
        dbus_call_cached(self.arduino_path, 'set_alias', 'rt_nrst', False)

    def release_stm32_reset(self):
        """Releases the reset line"""
        dbus_call_cached(self.arduino_path, 'set_alias', 'rt_nrst', True)

    def reset_stm32(self, enter_bootloader=False):
        """Boots the STM32 on the board, optionally will enter bootloader mode (though only if the board is actually powered on at this point...)"""
        if enter_bootloader:
            dbus_call_cached(self.arduino_path, 'set_alias', 'rt_boot0', True)
        else:
            dbus_call_cached(self.arduino_path, 'set_alias', 'rt_boot0', False)
        self.hold_stm32_reset()
        time.sleep(0.100)
        self.release_stm32_reset()
        if enter_bootloader:
            time.sleep(0.100)
            dbus_call_cached(self.arduino_path, 'set_alias', 'rt_boot0', False)

    def get_bootloader(self):
        """Shorthand for rebooting the STM32 to bootloader and cycling USB"""
        # See if we're lucky
        if self.usb_device_present(RT_DFU_DEVICEID):
            return True
        # Try again with USB enabled (TODO: wire a sense pin so we can know if USB has power or not)
        self.enable_usb(True)
        time.sleep(0.500)
        if self.usb_device_present(RT_DFU_DEVICEID):
            return True
        self.enable_usb(False)
        self.set_power(self.bootloader_voltage, self.bootloader_current) # Just in case something had readjusted the values
        self.reset_stm32(True)
        # Give the controller time to wake up
        time.sleep(0.100)
        self.enable_usb(True)
        # Make sure the serialport actually shows up on device tree
        timeout_start = time.time()
        while not self.usb_device_present(RT_DFU_DEVICEID):
            # It will take a few moments, no need to keep spawning shells as fast as the computer can
            time.sleep(1)
            if ((time.time() - timeout_start) > self.usb_device_present_timeout):
                raise RuntimeError("Could not find device %s in %f seconds" % (RT_DFU_DEVICEID, self.usb_device_present_timeout))
        return True

    def get_serialport_tty(self, devid):
        """returns the tty path for given device id (well the first one anyway)"""
        # TODO: Find out which /dev/ttyACM it got bound to and return that as string
        context = pyudev.Context()
        for device in context.list_devices(subsystem='tty', ID_VENDOR_ID=devid.split(':')[0], ID_MODEL_ID=devid.split(':')[1]):
            return device['DEVNAME']
        # TODO: Raise error ??
        return ''


    def get_serialport(self):
        """Shorthand for rebooting the STM32 and cycling USB"""
        if self.usb_device_present(RT_SERIAL_DEVICEID):
            return self.get_serialport_tty(RT_SERIAL_DEVICEID)
        # Try again with USB & module enabled (TODO: wire a sense pin so we can know if USB has power or not)
        self.hp6632b.set_output(True)
        if self.hp6632b.measure_voltage() < 3700: 
            self.set_power(4100, 50) # Just in case something had readjusted the values
        self.enable_usb(True)
        timeout_start = time.time()
        while not self.usb_device_present(RT_SERIAL_DEVICEID):
            # It will take a few moments, no need to keep spawning shells as fast as the computer can
            time.sleep(1)
            if ((time.time() - timeout_start) > 2.0):
                break
        # Still nothing, cycle USB, reset the board
        self.enable_usb(False)
        self.set_power(4100, 50) # Just in case something had readjusted the values
        self.reset_stm32()
        # Give the controller time to wake up
        time.sleep(0.100)
        self.enable_usb(True)
        # Make sure the serialport actually shows up on device tree
        timeout_start = time.time()
        while not self.usb_device_present(RT_SERIAL_DEVICEID):
            # It will take a few moments, no need to keep spawning shells as fast as the computer can
            time.sleep(1)
            if ((time.time() - timeout_start) > self.usb_device_present_timeout):
                raise RuntimeError("Could not find device %s in %f seconds" % (RT_SERIAL_DEVICEID, self.usb_device_present_timeout))
        return self.get_serialport_tty(RT_SERIAL_DEVICEID)

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
        self.log_data('','',short_pulse_count, '') # Do not waste time measuring voltage or current
        pass

    def open_logfile(self, headers=None):
        """Opens a timestamped logfile named after self.testname, and writes the first row as headers for CSV data. The file is buffered so you cannot tail it in realtime"""
        if not headers:
            headers = [u'Time',u'Voltage', u'Current', u'Syncpulses', u'Comment']
        suffix = self.testname
        if not suffix:
            suffix = os.path.basename(__file__)
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs', "%s_%s.csv" % (time.strftime("%Y-%m-%d_%H%M"), suffix))
        # Open buffered file stream
        self.log_handle = io.open(filename, mode='wb')
        # Make it CSV
        self.logger = csv.writer(self.log_handle)
        # And write the header
        self.logger.writerow(headers)

    def log_data(self, *args):
        """Logs arbitrary data to the logfile, the first column is automatically a timestamp though"""
        if not self.logger:
            self.open_logfile()
        row = [ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") ] + list(args)
        self.logger.writerow(row)

    def log_voltage_et_current(self):
        """Logs both voltage and current to the logfile"""
        self.log_data(self.hp6632b.measure_voltage(), self.hp6632b.measure_current(), '')
        return True

    def set_log_voltage_et_current_interval(self, ms):
        """Sets up a interval timer for logging voltage & current (and logs the first line immediately)"""
        self.log_voltage_et_current()
        self.voltage_timer = gobject.timeout_add(ms, self.log_voltage_et_current)
        return self.voltage_timer

    @timeout_decorator.timeout(COMPILE_TIMEOUT) # Uses sigalarm to make sure we don't deadlock
    def recompile(self, *args):
        """Runs ruuvi_build.sh, any extra arguments will be passed as args to the script"""
        pi_backup = None
        # This will mess up scons
        if os.environ.has_key('PYTHONINSPECT'):
            pi_backup = os.environ['PYTHONINSPECT']
            del(os.environ['PYTHONINSPECT'])
        cmd = [ "./ruuvi_build.sh" ]
        if len(args) > 0:
            cmd = cmd + list(args)
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..' )))
        output = p.communicate()
        # restore the pythoninspect if it was set
        if pi_backup:
            os.environ['PYTHONINSPECT'] = pi_backup
        # TODO: write to output to compile log
        #print " *** COMPILE OUTPUT *** \n%s\n*** /COMPILE OUTPUT ***" % output
        if p.returncode!= 0:
            print " *** COMPILE FAILED *** \n%s\n*** /COMPILE FAILED (cmd: %s, returncode: %d ***" % (output, repr(cmd), p.returncode)
            return False
        return True

    @timeout_decorator.timeout(FLASH_TIMEOUT) # Uses sigalarm to make sure we don't deadlock
    def flash(self, *args):
        """Runs ruuvi_program.sh, any extra arguments will be passed as args to the script, will call get_bootloader if the DFU device is not found. NOTE: this will disconnect USB (it needs to be cycled anyway to get the correct device enumerated)"""
        if not self.usb_device_present(RT_DFU_DEVICEID):
            self.get_bootloader()
        cmd = [ "./ruuvi_program.sh" ]
        if len(args) > 0:
            cmd = cmd + list(args)
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..' )))
        output = p.communicate()
        # TODO: write to output to flash log
        #print " *** FLASH OUTPUT *** \n%s\n*** /FLASH OUTPUT ***" % output
        if p.returncode != 0:
            print " *** FLASH FAILED *** \n%s\n*** /FLASH FAILED (cmd: %s, returncode: %d ***" % (output, repr(cmd), p.returncode)
            return False
        self.enable_usb(False)
        return True

    def usb_device_present(self, devid, expect_iproduct=None):
        """Checks if given USB device is present on the bus, optionally can verify the iProduct string"""
        # TODO: switch to udev, though it's a bit more complex (Especially for the RT DFU vs Serialport case...)
        if expect_iproduct:
            raise NotImplementedError("this check is not yet implemented")
        try:
            out = subprocess.check_output([ "lsusb", "-d %s" % devid, "-v" ])
            # TODO check output for the expected iProduct string
            return True
        except subprocess.CalledProcessError, e:
            if e.returncode == 1:
                return False
            # some other error, re-raise it
            raise e

    def hook_signals(self):
        """Hooks common UNIX signals to corresponding handlers"""
        signal.signal(signal.SIGTERM, self.quit)
        signal.signal(signal.SIGQUIT, self.quit)
        signal.signal(signal.SIGHUP, self.set_defaut_state)

    def defaults_setup(self):
        """You can change config variables here before set_defaut_state is called"""
        pass

    def copy_file(self, source, target):
        """Makes copies source to target, basically shutil.copyfile but adds the target to our cleanup list"""
        shutil.copyfile(source, target)
        self._cleanup_files.append(target)

    def copy_testcase_lua(self):
        """Copies the test helpers and the testcase lua script to romfs"""
        if not self.testname:
            raise RuntimeError("self.testname is not defined")
        romfs_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'romfs' ))
        testcases_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testcases' )
        self.copy_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testhelpers.lua'), os.path.join(romfs_path, 'testhelpers.lua'))
        self.copy_file(os.path.join(testcases_path, '%s.lua' % self.testname), os.path.join(romfs_path, 'autorun.lua'))

    def recompile_and_flash(self):
        """Mainly for manual testing without having to handle the module in the testrig"""
        self.recompile()
        self.flash()

    def copy_compile_flash(self):
        """Shorthand for calling copy_testcase_lua() recompile() flash() """
        self.copy_testcase_lua()
        self.recompile()
        self.flash()

    def setup(self):
        """Set up your test here"""
        pass    

    def run(self):
        """The actual test, you must enable the eventloop to receive DBUS messages (like sync signals from the board), remember to use set_runtime or set some other event to call quit() before starting the loop"""
        self.setup()
        self.run_eventloop()

    def set_runtime(self, seconds):
        """Sets the runtime for this test in seconds (actually "ticks" but one tick is one second) and starts the timer, calling this again will reset the tick count"""
        if not self._tick_timer:
            self._tick_timer = gobject.timeout_add(1000, self._tick)
        self._tick_count = 0
        self._tick_limit = seconds

    def _tick(self):
        """Counts ticks, used to track long-running tests and give a handy way to log for X seconds and quit"""
        self._tick_count += 1
        if (    self._tick_limit > 0
            and self._tick_count >= self._tick_limit):
            print """ *** Tick limit of %d reached, quitting *** """ % self._tick_limit
            self.quit()
        return True

    def run_eventloop(self):
        self.loop.run()

    def cleanup(self):
        """Cleans up files we copied to the build tree"""
        for f in self._cleanup_files:
            if not os.path.exists(f):
                continue
            print " * cleanup up file %s" % f
            os.unlink(f)

    def quit(self):
        """Tears down the SCPI connections, closes log handles and quits the mainloop"""
        self.loop.quit()
        self.hp6632b.quit()
        if self.log_handle:
            self.log_handle.close()
        self.cleanup()
