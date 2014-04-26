#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import sqlite3
# Decimal recipe from http://stackoverflow.com/questions/6319409/how-to-convert-python-decimal-to-sqlite-numeric
import decimal
import numpy as np
# Register the adapter
sqlite3.register_adapter(decimal.Decimal, lambda d: str(d))
# Register the converter (but we have to use np.float64 since coercing numpy object arrays to other types won't work)
sqlite3.register_converter("NUMERIC", lambda s:  np.float64(s))
# Register converter&adapter for datetime in the same way
import datetime
sqlite3.register_adapter(datetime.datetime, lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S.%f"))
# The type on SQLite is "TIMESTAMP" even if we specified "DATETIME" in table creation...
sqlite3.register_converter("TIMESTAMP", lambda s: datetime.datetime.strptime(s.ljust(26,"0"), "%Y-%m-%d %H:%M:%S.%f"))
# Initialize db connection
conn = sqlite3.connect(sys.argv[1], detect_types=sqlite3.PARSE_DECLTYPES)
c = conn.cursor()

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import time

class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        rng = datetime.timedelta(microseconds=(max(values)-min(values)))
        #print "tickStrings called, scale=%s, values=%s, spacing=%s, rng=%s" % (repr(scale), repr(values), repr(spacing), repr(rng))
        dtvalues = [ datetime.datetime.fromtimestamp(x / float(10**6)) for x in values ]

        # Visible range less than 20 s
        if (rng.seconds < 20):
           return [ x.strftime("%M:%S.%f") for x in dtvalues ]

        # Visible range is over one day
        if (rng.days > 1):
           return [ x.strftime("%m-%d %H:%M") for x in dtvalues ]
 
        return [ x.strftime("%m-%d %H:%M:%S") for x in dtvalues ]


app = pg.mkQApp()

axis = DateAxis(orientation='bottom')
vb = pg.ViewBox()

pw = pg.PlotWidget(viewBox=vb, axisItems={'bottom': axis}, enableMenu=True, title="")

c.execute("SELECT time,amps FROM current")
ampsdata = np.array(c.fetchall())

dates = np.arange(8) * (3600*24*356)
#print  ampsdata[:,0]

dates = np.array([ np.uint64(x.strftime("%s%f")) for x in ampsdata[:,0] ])
#print dates
pw.plot(x=dates, y=ampsdata[:,1], symbol='o')
pw.show()
pw.setWindowTitle('Current plot')


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
