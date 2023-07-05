import pytest
import sys
from time import sleep
import importlib.machinery
sys.path.insert(1, '../tasq_package')


# To run, simply type py.test in the same directory as this file
def test_simple():
    pass


# def test_get_utc_timestamp():
#     # added a comment
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
#
#
# def test_get_utc_timestamp_two():
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
#
#
#
# def test_get_utc_timestamp_three():
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
#
#
#
#
# def test_get_utc_timestamp_four():
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
#
#
#
# def test_get_utc_timestamp_five():
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
#
#
#
# def test_get_utc_timestamp_six():
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
#
#
#
# def test_get_utc_timestamp_seven():
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
#
#
#
# def test_get_utc_timestamp_eight():
#     pandas_timestamp = get_utc_timestamp(pd.to_datetime('2017-01-01 00:00:00'), 'America/Denver', pd.Timedelta('1h'))
#     ret = pandas_timestamp.isoformat()
#     ret = ret.split('+')[0]
#     sleep(0.5)
#     assert ret == '2017-01-01T07:00:00'
