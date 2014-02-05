#!/usr/bin/env python
import os,sys
# Put to interactive mode
#os.environ['PYTHONINSPECT'] = '1'

from rt_testcase import rt_testcase
import atexit

c = rt_testcase()
atexit.register(c.quit)

c.set_runtime(7)
c.enable_servos(True)
c.pan_from_to(20, 120, 3.0)
c.tilt_from_to(20, 120, 2.0)
c.tilt_from_to(120, 20, 2.0, 2500)
c.pan_from_to(120, 20, 3.0, 3000)

c.run_eventloop()
