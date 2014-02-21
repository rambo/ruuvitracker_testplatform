# Hardware

This is built from pieces of polycarbonate (because I had some laying around) mangled with a bandsaw and hot glue (because I ran out of suitable screws).
And various bits and pieces I happened to have. Some things I intend to re-use are attached with velcro rather than hot-glue, or with magnets (which in
turn are hot-glued)

  - 2 servos in a pan/tilt mount
  - FreArduino (Arduino Uno clone, but with extra pin headers)
  - Random relay card from DX
  - Spare USB hub and cable
  - Buttons, wires, breadboard, cable-ties, more hot glue...
  - A loaner HP 3362B programmable power supply (for the RuuviTracker, this is the "battery", also nice for very accurate current measurements)
  - A basic bench power supply (6.5V for the servos)

I'll draw some sort of schematics when I get around to it. There's one slightly tricky patch wire in RevC1 (boot0) you must solder even if you have a breakout
board for the hirose header (rest of the signals we need go trough that).

RevC2 has all the signals on board-edge connectors which is much nicer.
