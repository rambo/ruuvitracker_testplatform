#!/usr/bin/env python
"""Starts the board and oes 5 minute current profile, does not compile or flash anything"""

import os,sys
# Add the parent dir to search paths
libs_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ), '..')
if os.path.isdir(libs_dir):                                       
    sys.path.append(libs_dir)

from rt_testcase import rt_testcase


class five_minute_current_log(rt_testcase):
    def __init__(self, *args, **kwargs):
        super(five_minute_current_log, self).__init__(*args, **kwargs)
        self.testname = 'five_minute_current_log'

    def setup(self):
        self.hp6632b.display_on(False) # Conserve display
        self.set_log_current_interval(50)
        self.set_log_voltage_interval(500)
        self.set_runtime(300) # 5 minutes
        self.set_power(4100, 1000)

if __name__ == '__main__':
    test = five_minute_current_log()
    print " ***** START ***** "
    test.run()
    print " ***** DONE ***** "

