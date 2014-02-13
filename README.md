ruuvitracker_testplatform
=========================

Automatic test platform for RuuviTracker

Using the (currently) one and only test rig by rambo

## Dependencies

    sudo apt-get install python-pyudev

### Dependencies without apt packages

  - <https://github.com/rambo/arDuBUS>
  - <https://github.com/rambo/python-scpi>
  - <https://pypi.python.org/pypi/timeout-decorator>

## TODO

### Fix the assumptions

  - Add YAML config for locations like the RT source/build dir
  - Do not assume eLua (or make branches for chibios vs elua ??)
