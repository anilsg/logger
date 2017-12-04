#!/usr/bin/env python
# Python 3.6.3

"""
Remote logging server cache collector converts cached messages into the final log files.
The remote logging server receives messages and drops them quickly into the cache.
This/these workers then aggregate the cached messages and feed them into specific log files.

1. Messages are put into the cache by the logging server at one file per one message named: YYYYMMDD-HHMMSS.uuuuuu-levelno-facility
2. This message_collector then moves blocks of messages into a per process, per day, temporary directory, to isolate them.
   Directories are per process to eliminate the need for locking.
   Directories are per day to partition message stream into discrete days for processing, and to simplify clean up.
3. This message_collector then adds the isolated messages to the appropriate log files.
   Log files exist per day, per level, per facility, to support querying.
   Log files are named: YYYYMMDD-levelno-facility.
   The individual message files are destroyed.
4. This message_collector performs appropriate clean up at intervals.

TODO: Draw directory structure diagram here in this doc string.
TODO: Various degrees of sophistication for improving throughput.
TODO: E.g. Manage a dedicated sub-process per log file to keep the log file open and aggregate selectively from cache to that file.
TODO: Expiry of finished log files and removal from the server at automated intervals.
"""

import os
import datetime
import time

log_path = '/srv/logger'
pids_path = os.path.join(log_path, 'pids') # Directories will be at /srv/logger/pids/<YYYYMMDD>/<pid>/.
cache_directory = os.path.join(log_path, 'cache') # Message files dropped in this directory by server.
log_directory = os.path.join(log_path, 'logs') # Message files dropped in this directory by server.

if __name__ == '__main__':
    try:
        while True:

            # Create day temporary directory for this process only.
            now = datetime.datetime.now(datetime.timezone.utc)
            today = '{0:%Y%m%d}'.format(now) # Get an ISO order date string YYYYMMDD.
            pid = str(os.getpid()) # Get this process ID as a string.
            pid_directory = os.path.join(pids_path, today, pid) # Determine day/pid directory.
            os.makedirs(pid_directory, exist_ok=True) # Make or remake /srv/logger/pids/<YYYYMMDD>/<pid>/.

            # Clean up two days and older empty temporary directories.
            yesterday = '{0:%Y%m%d}'.format(now - datetime.timedelta(1)) # Date time 24 hours ago.
            for day in os.listdir(pids_path): # Look for old temporary day directories.
                if day < yesterday: # Two or more days old. These directories will now be static.
                    try: # Try to delete the old directories.
                        pids = os.listdir(os.path.join(pids_path, day)) # Pid directories inside the old day directory.
                        for pid in pids + ['']: # All the pid directories and an extra entry for the parent day directory.
                            os.removedirs(os.path.join(pids_path, day, pid)) # Recursive delete won't delete files.
                    except Exception as e: # Won't remove directories if files still exist in them.
                        pass # Shouldn't be any files left. This should automatically remove all old pid directories.
            
            # Check for candidate messages in cache.
            message_list = os.listdir(cache_directory)
            print("messages", len(message_list)) ## Testing / debug.
            if not len(message_list): # Nothing to do.
                time.sleep(5) # Must be a quiet period.
                continue # Restart full process in order to handle day rollover.

            # Move some messages from initial server cache to per day, per process temporary directory.
            message_list.sort() # Get oldest messages first.
            for message_name in message_list: # Message name format supports date order sorting: YYYYMMDD-HHMMSS.uuuuuu-levelno-facility
                try:
                    os.rename(os.path.join(cache_directory, message_name), os.path.join(pid_directory, message_name))
                    break ## Testing / debug one at a time. Remove this later for bulk processing.
                except: # Any failure aborts further processing.
                    break # But messages already isolated still need to be processed.

            # Check for isolated messages, if any.
            message_list = os.listdir(pid_directory)
            if not len(message_list): # Didn't actually take any this time.
                continue # No need to pause, potentially another process took some messages.

            # Catenate all isolated message content into the appropriate log file.
            # Current implementation does not share log files out. Currently only one process.
            log_files = dict() # Open each log file only once on this iteration.
            message_list.sort() # Log messages in date time order.
            for message_name in message_list: # Append messages to a log file one at a time.

                # Open or get previously opened log file.
                log_name = message_name.split('-') # Determine and construct associated log file name.
                log_name = '-'.join((log_name[0], log_name[2], log_name[3])) # YYYYMMDD-levelno-facility.
                log_file = log_files.setdefault(log_name, open(os.path.join(log_directory, log_name), mode='ab')) # TODO: Protection from open failure.

                # Append message content from message file into the log file.
                with open(os.path.join(pid_directory, message_name), mode='rb') as message_file:
                    log_file.write(message_file.read()) # No need to decode, treat as binary is faster.

                # Remove copied message file.
                os.remove(os.path.join(pid_directory, message_name))

            # Close all log files before next iteration.
            for log_file in log_files:
                log_files[log_file].close()

    except KeyboardInterrupt:
        pass

