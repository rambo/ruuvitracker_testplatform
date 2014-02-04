#!/usr/bin/env python
"""This simply compiles and flashes whatever is in the source tree now, does copy any test scripts to romfs"""

import os,sys
# Add the parent dir to search paths
libs_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ), '..')
if os.path.isdir(libs_dir):                                       
    sys.path.append(libs_dir)

from rt_testcase import rt_testcase


class no_test(rt_testcase):
    def __init__(self, *args, **kwargs):
        super(no_test, self).__init__(*args, **kwargs)
        self.testname = 'no_test'

    def setup(self):
        self.recompile_and_flash()
        self.quit()

if __name__ == '__main__':
    test = no_test()
    print " ***** START ***** "
    test.run()
    print " ***** DONE ***** "

