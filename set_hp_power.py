#!/usr/bin/env python
import sys,os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from exceptions import NotImplementedError,RuntimeError
from scpi.devices import hp6632b
from dbushelpers.call_cached import call_cached as dbus_call_cached


arduino_path = "/fi/hacklab/ardubus/ruuvitracker_tester"
loop = gobject.MainLoop()
bus = dbus.SessionBus()
# Make sure the HP is powered
dbus_call_cached(arduino_path, 'set_alias', 'hp_power', bool(int(sys.argv[1])))
