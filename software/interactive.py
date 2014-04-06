#!/usr/bin/env python
import os,sys
# Put to interactive mode
os.environ['PYTHONINSPECT'] = '1'

from rt_testcase import rt_testcase
from dbushelpers.call_cached import call_cached as dbus_call_cached
import atexit

c = rt_testcase()
atexit.register(c.quit)
#c.get_serialport()

hp = c.hp6632b
#c.set_log_voltage_et_current_interval(50) # Requires HW-flow control, but so does the serial interface these days
#c.run_eventloop()
