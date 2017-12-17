#!/usr/bin/env python

import os
log_path = '/srv/logger'
log_directory = os.path.join(log_path, 'logs') # Available logs.

def get_counts():
    """
    E.g. curl -i http://localhost:8080/api/v1/counts/20171205/02/?name=facility_one
    /api/v1/counts/YYYYMMDD[HH[MM]]/DD[HH[MM]]/[levelno[-levelno]]/[facility_name]
    1. breakdown URL into parts
    2. cycle through available files
    3. if match level, facility, date
    4. open read count matching lines
    """
    url = '/api/v1/counts/YYYYMMDD-HHMMSS/YYYYMMDD-HHMMSS/level-level/facility_name...'
    since = '20171205-134200'
    until = '20171205-134223'
    levels = '30-40'
    facility = 'facility_one'

    since, start_time = since.split('-')
    until, stop_time = until.split('-')
    start_level, stop_level = levels.split('-')
    facilities = (facility,)

    message_count = 0
    log_list = os.listdir(log_directory)
    for log_name in log_list:
        (day, level, facility) = log_name.split('-')
        if day < since: continue
        if day > until: break
        if level < start_level: continue
        if level > stop_level: continue
        if facility not in facilities: continue
        print("reading", log_name) # DEBUG
        start_time = day == since and start_time or ''
        stop_time = day == until and stop_time or ''
        with open(os.path.join(log_directory, log_name), mode='r') as log_file:
            for log_line in log_file:
                stamp = log_line.split('.')[0].split('-')[1]
                if start_time and stamp < start_time: continue
                if stop_time and stamp > stop_time: continue
                message_count += 1
    return message_count

print(get_counts())
