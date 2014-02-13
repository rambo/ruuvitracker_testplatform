--[[--
Helpers for testcases
--]]--

local testmodule = {}
testmodule.pulsepin = pio.PB_0
pio.pin.setdir(pio.OUTPUT, testmodule.pulsepin)

function testmodule.send_syncpulses(num_pulses)
    -- Sends one long pulse, then num_pulses short ones, then a long pulse, used for syncing with the test script running on the computer
    testmodule.send_pulse(5)
    for pulse=1,num_pulses
    do
        -- We get slightly under one ms delay anyway, but this should make it more constant
        ruuvi.delay_ms(1)
        testmodule.send_pulse(2)
    end
    ruuvi.delay_ms(1)
    testmodule.send_pulse(5)
end

function testmodule.send_pulse(msec)
    -- Pulse the debug pin for given amount of milliseconds
    pio.pin.sethigh(testmodule.pulsepin)
    ruuvi.delay_ms(msec)
    pio.pin.setlow(testmodule.pulsepin)
end

return testmodule
