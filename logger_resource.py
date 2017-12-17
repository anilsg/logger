#!/usr/bin/env python
# Python 3.6.3
# logger_resource.py

"""
logger_resource.py:
Read and respond to GET requests.
Called by logger_httpd.py.
"""

import os

log_path = '/srv/logger'
log_directory = os.path.join(log_path, 'logs') # Available logs.

def split_min(req, sep='/', minvals=4):
    """
    Split a string and generate additional empty string entries up to the specified minimum number of values.
    """
    for tok in req.split(sep):
        minvals -= 1
        yield tok
    while minvals > 0:
        minvals -= 1
        yield ''


class GetFilter():
    """
    Respond to GET requests to return messages, counts and ranges of values available.
    Only counts implemented so far.
    When creating new instance supply url /api/v1/<resource>/<since>/<until>/<levels>/<facility_name>/<facility_name>/...
    Where <since> and <until> are date/times of the form "YYYYMMDD-HHMMSS".
    Where <levels> are expressed as double digit numbers either an individual level "LL" or a range "LL-MM".
    Values omitted are taken to mean "including all".
    E.g. '/api/v1/counts/20171205-130000/20171205-135959/30-40/facility_one'

    TODO: Strip superfluous empty strings in facilities list generated from trailing slash in URL.
    TODO: GET Ranges.
    TODO: GET Messages.
    """

    def __init__(self, url='/api/v1/counts'):
        """
        Break down URL into component parameters and assign to useful class attributes.
        """
        url = url[8:] # Chop of invariant URL leader '/api/v1/'. URL now starts at resource.
        (self.resource, since, until, levels, *facilities) = split_min(url, sep='/', minvals=4) # Split out the URL.
        (self.since, self.start_time) = split_min(since, sep='-', minvals=2) # Split start day and time.
        (self.until, self.stop_time) = split_min(until, sep='-', minvals=2) # Split out end day and time.
        (self.start_level, self.stop_level) = split_min(levels, sep='-', minvals=2) # Look for range of levels.
        self.facilities = facilities # Assigning to *facilities forces facilities to a list.

    def get_counts(self):
        """
        Read all logs matching the filter and count matching lines.
        Uses self.since, self.start_time, self.until, self.stop_time,
        self.start_level, self.stop_level, self.facilities.
        """
        message_count = 0 # Count matching lines / messages.
        log_list = os.listdir(log_directory) # List of log file names.
        for log_name in log_list: # Check each log file for inclusion.
            (day, level, facility) = log_name.split('-') # Log file name describes it's content.
            if self.since and day < self.since: continue # If self.since defined, do not include earlier messages.
            if self.until and day > self.until: break # If self.until not defined, include all messages.
            if self.start_level and level < self.start_level: continue # Filter out unselected levels.
            if self.stop_level and level > self.stop_level: continue # /LL/ should be the same as /LL-LL/.
            if self.facilities and facility not in self.facilities: continue # Any number of facility names can be included.
            start_time = day == self.since and self.start_time or '' # Start time only applies on the first day in the range.
            stop_time = day == self.until and self.stop_time or '' # End time only applies on the last day in the range.
            with open(os.path.join(log_directory, log_name), mode='r') as log_file:
                for log_line in log_file: # Check every line in every selected log file.
                    stamp = log_line.split('.')[0].split('-')[1]
                    if start_time and stamp < start_time: continue
                    if stop_time and stamp > stop_time: continue
                    message_count += 1 # Count all lines meeting the filter criteria.
        self.message_count = message_count # Set the total message count.


if __name__ == '__main__': # Just for testing.
    url = '/api/v1/counts/20171205-134200/20171205-134223/30-40/facility_one/facility_two/facility_three/'
    filtered = GetFilter(url)
    print(filtered.facilities)
    filtered.get_counts()
    print(filtered.message_count)
