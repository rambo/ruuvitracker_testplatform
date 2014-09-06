#!/usr/bin/env python
"""Intended for the debug version of tracker.c, runs as long as the tracker keeps sending sync pulses"""

import os,sys
# Add the parent dir to search paths
libs_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ), '..')
if os.path.isdir(libs_dir):                                       
    sys.path.append(libs_dir)

from rt_testcase import rt_testcase
import time, datetime

class endurance(rt_testcase):
    def __init__(self, *args, **kwargs):
        super(endurance, self).__init__(*args, **kwargs)
        self.testname = 'no_test'
        self.last_keepalive = None

    def setup(self):
        self.hp6632b.display_on(False) # Conserve display
        self.set_power(4100,2000)
        self.set_log_only_current_interval(100)
        # Start first with 15s timeout (when we receive the pulses we'll reset this timer)
        self.keepalive_timer = gobject.timeout_add(1500, self.verify_keepalive) # We ought to get the first one immediately

    def verify_keepalive(self):
        from exceptions import RuntimeError
        if not self.last_keepalive:
            raise RuntimeError("No keepalive seen for at all")
        if (time.time() - self.last_keepalive > 20):
            raise RuntimeError("No keepalive seen for 20s")
        return True 

    def sync_received(self, short_pulse_count):
        super(endurance, self).sync_received(short_pulse_count)
        if short_pulse_count == 10:
            print "  Keepalive seen at %s" % datetime.datetime.now().isoformat()
            self.last_keepalive = time.time()
            # Remove the old event, add new
            gobject.source_remove(self.keepalive_timer)
            self.keepalive_timer = gobject.timeout_add(5000, self.verify_keepalive)
        
        

if __name__ == '__main__':
    test = endurance()
    print " ***** START ***** "
    test.run()
    print " ***** DONE ***** "

