#!/usr/bin/env python
# Python 3.6.3

"""
Remote logging server cache collector.
Remote logging server receives messages and drops them quickly into the cache.
This/these workers aggregate the cached messages and feed them into specific log files.

Messages are received into the cache as one file per one message named: YYYYMMDD-HHMMSS.uuuuuu-levelno-facility

TODO: Various degrees of sophistication for improving throughput.
TODO: E.g. Manage a dedicated sub-process per log file to keep the log file open and aggregate selectively from cache to that file.
"""

import os
import time

cache_directory = '/srv/http/logger/cache'

if __name__ == '__main__':
    try:
        while True:
            
            # Check for candidate messages in cache.
            message_list = os.listdir(cache_directory)
            print("messages", len(message_list))
            time.sleep(5)


    except KeyboardInterrupt:
        pass

