#!/usr/bin/env python
"""Testing pyqtgraph with data from sqlite"""
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
sqlite3.register_adapter(datetime.datetime, lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S.%f")) # This actually gives incorrect result since it supposed the padding that is not in sqlite...
sqlite3.register_converter("DATETIME", lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")) # This actually gives incorrect result since it supposed the padding that is not in sqlite...
# Initialize db connection
conn = sqlite3.connect(sys.argv[1], detect_types=sqlite3.PARSE_DECLTYPES)
c = conn.cursor()

# Import the graphing stuff
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

# From the examples
class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strns = []
        rng = max(values)-min(values)
        #if rng < 120:
        #    return pg.AxisItem.tickStrings(self, values, scale, spacing)
        if rng < 3600*24:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        elif rng >= 3600*24 and rng < 3600*24*30:
            string = '%d'
            label1 = '%b - '
            label2 = '%b, %Y'
        elif rng >= 3600*24*30 and rng < 3600*24*30*24:
            string = '%b'
            label1 = '%Y -'
            label2 = ' %Y'
        elif rng >=3600*24*30*24:
            string = '%Y'
            label1 = ''
            label2 = ''
        for x in values:
            try:
                strns.append(time.strftime(string, time.localtime(x)))
            except ValueError:  ## Windows can't handle dates before 1970
                strns.append('')
        try:
            label = time.strftime(label1, time.localtime(min(values)))+time.strftime(label2, time.localtime(max(values)))
        except ValueError:
            label = ''
        #self.setLabel(text=label)
        return strns
# This segfaults for some reason...
#daxis = DateAxis(orientation='bottom')


win = pg.GraphicsWindow(title="Voltage & current plots")


c.execute("SELECT time,volts FROM voltage")
voltsdata = np.array(c.fetchall())
voltsplot = win.addPlot(title="Voltage")
#voltsplot.plot(voltsdata[:,0],voltsdata[:,1])
voltsplot.plot(voltsdata[:,1])

win.nextRow()

c.execute("SELECT time,amps FROM current")
ampsdata = np.array(c.fetchall())
#ampsplot = win.addPlot(title="Current", axisItems={'bottom': axis})
#ampsplot.plot(ampsdata[:,0],ampsdata[:,1])
ampsplot = win.addPlot(title="Current")
ampsplot.plot(ampsdata[:,1])

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
