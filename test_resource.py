#!/usr/bin/env python
"""
Test logger_resource.py.

Anil Gulati
01/09/2018
"""

import logger_resource

def test_split_min_empty_default():
    assert list(logger_resource.split_min('')) == ['', '', '', '']

def test_split_min_empty_3():
    assert list(logger_resource.split_min('', minvals=3)) == ['', '', '']

def test_split_min_standard():
    assert list(logger_resource.split_min('/api/v1/counts/20171205-134200/20171205-134223/30-40/facility_one'[8:])) == ['counts', '20171205-134200', '20171205-134223', '30-40', 'facility_one']

def test_split_min_override_defaults():
    assert list(logger_resource.split_min('20171205-134200', sep='-', minvals=2)) == ['20171205', '134200']

def test_split_min_missing_values():
    assert list(logger_resource.split_min('20171205', sep='-', minvals=2)) == ['20171205', '']

def test_get_filter_init():
    filtered = logger_resource.GetFilter('/api/v1/counts/20171205-134200/20171205-134223/30-40/facility_one/facility_two/facility_three/')
    assert filtered.facilities == ['facility_one', 'facility_two', 'facility_three', '']

