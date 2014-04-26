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
conn = sqlite3.connect("plotdata.sqlite", detect_types=sqlite3.PARSE_DECLTYPES)
c = conn.cursor()

# Import the graphing stuff
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

c.execute("SELECT time,volts FROM voltage")
voltsdata = np.array(c.fetchall())
plt.plot(voltsdata[:,0],voltsdata[:,1], '.-')

c.execute("SELECT time,amps FROM current")
ampsdata = np.array(c.fetchall())
x = ampsdata[:,0]
y = ampsdata[:,1]
plt.plot(x,y, '.-')

plt.grid(True)

# Show millisecond datetimes
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S.%f"))
plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

plt.show()
