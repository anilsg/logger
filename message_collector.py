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

pids_path = '/srv/http/logger/pids' # Directories will be at /srv/http/logger/pids/<YYYYMMDD>/<pid>/.
cache_directory = '/srv/http/logger/cache' # Message files dropped in this directory by server.

if __name__ == '__main__':
    try:
        while True:

            # Create day temporary directory for this process only.
            now = datetime.datetime.now(datetime.timezone.utc)
            today = '{0:%Y%m%d}'.format(now) # Get an ISO order date string YYYYMMDD.
            pid = str(os.getpid()) # Get this process ID as a string.
            pid_directory = os.path.join(pids_path, today, pid) # Determine day/pid directory.
            os.makedirs(pid_directory, exist_ok=True) # Make or remake /srv/http/logger/pids/<YYYYMMDD>/<pid>/.
            
            # Check for candidate messages in cache.
            message_list = os.listdir(cache_directory)
            print("messages", len(message_list))
            time.sleep(5)


    except KeyboardInterrupt:
        pass

