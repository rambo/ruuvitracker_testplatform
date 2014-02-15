#!/usr/bin/env python
import sys,os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from dbushelpers.call_cached import call_cached as dbus_call_cached


arduino_path = "/fi/hacklab/ardubus/ruuvitracker_tester"
loop = gobject.MainLoop()
bus = dbus.SessionBus()
dbus_call_cached(arduino_path, 'set_alias', 'usb_power', bool(int(sys.argv[1])))
