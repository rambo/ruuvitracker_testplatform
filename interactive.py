#!/usr/bin/env python -i

from rt_testcase import rt_testcase
import atexit

c = rt_testcase()
atexit.register(c.quit)
c.get_serialport()
