#!/usr/bin/env python
"""Simple test to log idle current"""

import os,sys
# Add the parent dir to search paths
libs_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ),  '..', '..')
if os.path.isdir(libs_dir):                                       
    sys.path.append(libs_dir)

from rt_testcase import rt_testcase


class idle_current(rt_testcase):
    def __init__(self, *args, **kwargs):
        super(idle_current, self).__init__(*args, **kwargs)


