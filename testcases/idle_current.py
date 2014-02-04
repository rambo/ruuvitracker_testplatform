#!/usr/bin/env python
"""Simple test to log idle current"""

import os,sys
# Add the parent dir to search paths
libs_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ), '..')
if os.path.isdir(libs_dir):                                       
    sys.path.append(libs_dir)

from rt_testcase import rt_testcase


class idle_current(rt_testcase):
    def __init__(self, *args, **kwargs):
        super(idle_current, self).__init__(*args, **kwargs)
        self.testname = 'idle_current' # Makes easier to figure out which lua file to copy...


    def setup(self):
        self.copy_compile_flash()
        self.hold_stm32_reset() # Hold the MCU in reset untill we're ready to continue
        self.enable_usb(False)
        self.set_power(4100, 500)
        self.set_runtime(30) # Log extra 10s over the normal test run time.
        # Expect the first sync very soon, if not abort.
        self.expect_sync_in(1000)
        self.release_stm32_reset()

    def sync_received(self, short_pulse_count):
        print "*** idle_current: got sync of %d pulses ***" % short_pulse_count
        comment = ''
        if short_pulse_count == 1:
            comment = 'SD card on'
            self.set_log_voltage_et_current_interval(1000)
        if short_pulse_count == 2:
            comment = 'SD card off'
        if short_pulse_count == 3:
            comment = 'End of test program (sd-card re-enabled, control drops to eLua shell)'
        self.log_data('','',short_pulse_count, comment)


if __name__ == '__main__':
    test = idle_current()
#    import atexit
#    atexit.register(test.quit)
    print " ***** START ***** "
    test.run()
    print " ***** DONE ***** "

