#!/usr/bin/env python
# Python 3.6.3
# logger_collector.py

"""
logger_collector.py:
Remote logging cache collector adds cached messages onto the appropriate log files.
This process runs separately on the server in addition to logger_httpd.py.

Take individual message files dropped in /srv/logger/cache/ by logger_httpd.py.
Move the message files to /srv/logger/pids/YYYYMMDD/pid_number/.
Add messages to log files /srv/logger/logs/YYYYMMDD-LL-facility_name.

Anil Gulati
01/09/2018

TODO: Expiry of finished log files and removal from the server at automated intervals.
TODO: Can manage dedicated processes per log file to make use of more cores and achieve other efficiencies if throughput needs to be increased.
TODO: Add protection from failure to open log file errors.
"""

import os
import datetime
import time

log_path = '/srv/logger'
cache_directory = os.path.join(log_path, 'cache') # Message files initially dropped in this directory by logger_httpd.py.
pids_path = os.path.join(log_path, 'pids') # Secondary caches in here at /srv/logger/pids/<YYYYMMDD>/<pid>/.
log_directory = os.path.join(log_path, 'logs') # Actual log files stored in this directory.

if __name__ == '__main__': # Run python logger_collector.py in addition to python logger_httpd.py.
    try:
        while True: # Runs until manually interrupted.

            # Create day temporary directory for this process only.
            # Will only create it if it hasn't already been created.
            now = datetime.datetime.now(datetime.timezone.utc)
            today = '{0:%Y%m%d}'.format(now) # Get an ISO order date string YYYYMMDD.
            pid = str(os.getpid()) # Get this process ID as a string.
            pid_directory = os.path.join(pids_path, today, pid) # Determine day/pid directory.
            os.makedirs(pid_directory, exist_ok=True) # Make or remake /srv/logger/pids/<YYYYMMDD>/<pid>/.

            # Clean up two days and older empty temporary directories.
            # These old secondary cache directories should be empty and no longer used.
            yesterday = '{0:%Y%m%d}'.format(now - datetime.timedelta(1)) # Date time 24 hours ago.
            for day in os.listdir(pids_path): # Look for old temporary day directories.
                if day < yesterday: # Two or more days old. These directories will now be static.
                    try: # Try to delete the old directories.
                        pids = os.listdir(os.path.join(pids_path, day)) # Pid directories inside the old day directory.
                        for pid in pids + ['']: # All the pid directories and an extra entry for the parent day directory.
                            os.removedirs(os.path.join(pids_path, day, pid)) # Recursive delete won't delete files.
                    except Exception as e: # Won't remove directories if files still exist in them.
                        pass # Shouldn't be any files left. This should automatically remove all old pid directories.
            
            # Check for new candidate messages in the primary cache.
            # Dares to sleep for 5 seconds if nothing there.
            message_list = os.listdir(cache_directory)
            if not len(message_list): # Nothing to do.
                time.sleep(5) # Must be a quiet period. Use sleep(1 or 2) instead?
                continue # Restart full process in order to handle day rollover.

            # Move some messages from initial server cache to per day, per process secondary cache.
            # On day rollover doesn't matter if yesterday's pid directory is used for some messages.
            message_list.sort() # Get oldest messages first.
            for message_name in message_list: # Message name format supports date order sorting: YYYYMMDD-HHMMSS.uuuuuu-levelno-facility
                try:
                    os.rename(os.path.join(cache_directory, message_name), os.path.join(pid_directory, message_name))
                except: # Any failure aborts further processing. Unprocessed messages will be re-attempted later.
                    break # Messages already isolated still need to be processed.

            # Check for captured messages in secondary cache, if any.
            message_list = os.listdir(pid_directory)
            if not len(message_list): # Didn't actually take any messages this time for some reason.
                continue # No need to pause, potentially another process took some messages.

            # Catenate all isolated message content into the appropriate log file.
            # Current implementation does not share log files out, only one process.
            log_files = dict() # Open each log file only once on this iteration.
            message_list.sort() # Log messages in date time order.
            for message_name in message_list: # Append messages to a log file one at a time.

                # Open or get previously opened log file according to constructed log filename.
                log_name = message_name.split('-') # Message name is the individual message filename: YYYYMMDD-HHMMSS.uuuuuu-levelno-facility.
                log_name = '-'.join((log_name[0], log_name[2], log_name[3])) # Throw away the time when forming log filename YYYYMMDD-levelno-facility.
                log_file = log_files.setdefault(log_name, open(os.path.join(log_directory, log_name), mode='ab')) # dict.setdefault only opens if not already opened.
                # TODO: Protection from open failure.

                # Append message content from message file into the log file.
                with open(os.path.join(pid_directory, message_name), mode='rb') as message_file: # Open, read and close message file.
                    log_file.write(message_file.read()) # No need to decode, treat as binary is faster.

                # Remove copied message file.
                os.remove(os.path.join(pid_directory, message_name))

            # Close all log files before next iteration.
            for log_file in log_files:
                log_files[log_file].close()

    except KeyboardInterrupt:
        pass

