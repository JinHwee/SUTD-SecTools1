"""
Last Update: 3/11/2023 11:49 PM
@author: Mohamed Meeran
"""
import time
import datetime as dt
def events_per_second():
    start_time = dt.datetime.today().timestamp()
    i = 0
    while(True):
        time.sleep(0.1)
        time_diff = dt.datetime.today().timestamp() - start_time
        i += 1
        return i/time_diff
