-- Helpers
th = require "testhelpers"

-- Disable charger
chg = require "charger"
chg.disable()

-- We'll need this later
sd = require "sdcard"

-- Send first syncpoint, then delay (which does some sort of sleep on the MCU) for 10s
th.send_syncpulses(1)
ruuvi.delay_ms(10000)

-- Disable SD-Card power
sd.disable()
-- Send second syncpoint, then sleep for 10s
th.send_syncpulses(2)
ruuvi.delay_ms(10000)

-- Third syncpoint and re-enable sdcard.
th.send_syncpulses(3)
sd.enable()
