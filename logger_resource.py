#!/usr/bin/env python

import os
log_path = '/srv/logger'
log_directory = os.path.join(log_path, 'logs') # Available logs.

def split_min(req, sep='/', minvals=3):
    for tok in req.split(sep):
        minvals -= 1
        yield tok
    while minvals > 0:
        minvals -= 1
        yield ''

class get_filter():
    """
    Instead of since duration use since until
    /api/v1/counts/since/until/levels/names
    url = '/api/v1/counts/20171205-134200/20171205-134223/30-40/facility_one'
    TODO: Strip empty strings from facilities list generated from trailing slash in URL.
    """
    def __init__(self, url='/api/v1/counts'):
        url = url[8:]
        (self.resource, since, until, levels, *facilities) = split_min(url, sep='/', minvals=4)
        (self.since, self.start_time) = split_min(since, sep='-', minvals=2)
        (self.until, self.stop_time) = split_min(until, sep='-', minvals=2)
        (self.start_level, self.stop_level) = split_min(levels, sep='-', minvals=2)
        self.facilities = facilities

    def get_counts(self):
        """
        E.g. curl -i http://localhost:8080/api/v1/counts/20171205/02/?name=facility_one
        /api/v1/counts/YYYYMMDD[HH[MM]]/DD[HH[MM]]/[levelno[-levelno]]/[facility_name]
        1. breakdown URL into parts
        2. cycle through available files
        3. if match level, facility, date
        4. open read count matching lines
        Allow empty non supplied values to indicate 'all'.
        self.since, self.start_time, self.until, self.stop_time
        self.start_level, self.stop_level, self.facilities
        """
        message_count = 0
        log_list = os.listdir(log_directory)
        for log_name in log_list:
            (day, level, facility) = log_name.split('-')
            if self.since and day < self.since: continue
            if self.until and day > self.until: break
            if self.start_level and level < self.start_level: continue
            if self.stop_level and level > self.stop_level: continue
            if self.facilities and facility not in self.facilities: continue
            start_time = day == self.since and self.start_time or ''
            stop_time = day == self.until and self.stop_time or ''
            with open(os.path.join(log_directory, log_name), mode='r') as log_file:
                for log_line in log_file:
                    stamp = log_line.split('.')[0].split('-')[1]
                    if start_time and stamp < start_time: continue
                    if stop_time and stamp > stop_time: continue
                    message_count += 1
        self.message_count = message_count

if __name__ == '__main__':
    url = '/api/v1/counts/20171205-134200/20171205-134223/30-40/facility_one/facility_two/facility_three/'
    filtered = get_filter(url)
    print(filtered.facilities)
    filtered.get_counts()
    print(filtered.message_count)
