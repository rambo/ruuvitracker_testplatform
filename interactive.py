#!/usr/bin/env python -i

from rt_testcase import rt_testcase
import atexit

c = rt_testcase()
atexit.register(c.quit)
c.get_serialport()

#c.set_log_voltage_et_current_interval(1500) # apparently doing this too fast will kill the serial interface
#c.run_eventloop()
