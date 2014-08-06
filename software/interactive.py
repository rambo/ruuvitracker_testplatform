#!/usr/bin/env python
import os,sys
import time
# Put to interactive mode
os.environ['PYTHONINSPECT'] = '1'

from rt_testcase import rt_testcase
from dbushelpers.call_cached import call_cached as dbus_call_cached
import atexit

c = rt_testcase()
atexit.register(c.quit)
#c.get_serialport()

hp = c.hp6632b
# Tilt top towards camera
c.enable_servos()
c.set_tilt(110)
time.sleep(1)
c.enable_servos(False)

#c.set_log_voltage_et_current_interval(1500) # apparently doing this too fast will kill the serial interface
#c.run_eventloop()
