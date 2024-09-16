import unittest
from typing import List

from timespent import *


class MyTestCase(unittest.TestCase):
    one_week_of_noons: List[dict] = [
        {"date_time_field": "2021-09-01T12:00:00Z"},
        {"date_time_field": "2021-09-02T12:00:00Z"},
        {"date_time_field": "2021-09-03T12:00:00Z"},
        {"date_time_field": "2021-09-04T12:00:00Z"},
        {"date_time_field": "2021-09-05T12:00:00Z"},
        {"date_time_field": "2021-09-06T12:00:00Z"},
        {"date_time_field": "2021-09-07T12:00:00Z"}
    ]
    every_ten_minutes_for_the_1st_hour_of_september_1st: List[dict] = [
        {"date_time_field": "2021-09-01T00:00:00Z"},
        {"date_time_field": "2021-09-01T00:10:00Z"},
        {"date_time_field": "2021-09-01T00:20:00Z"},
        {"date_time_field": "2021-09-01T00:30:00Z"},
        {"date_time_field": "2021-09-01T00:40:00Z"},
        {"date_time_field": "2021-09-01T00:50:00Z"},
        {"date_time_field": "2021-09-01T01:00:00Z"}
    ]

    def test_map_dicts_to_work_sessions(self):
        seven_sessions_one_for_each_day = map_dicts_to_work_sessions(
            self.one_week_of_noons,
            date_time_field="date_time_field",
        )
        self.assertEqual(len(seven_sessions_one_for_each_day), 7)
        one_session_all_sessions_combined = map_dicts_to_work_sessions(
            self.one_week_of_noons,
            date_time_field="date_time_field",
            minutes=24 * 60
        )
        self.assertEqual(len(one_session_all_sessions_combined), 1)

    def test_calculate_timespent(self):
        all_week_separate_sessions = calculate_timespent_as_hours(
            self.one_week_of_noons,
            date_time_field="date_time_field"
        )
        self.assertEqual(1.75, all_week_separate_sessions)
        only_weekdays = calculate_timespent_as_hours(
            self.one_week_of_noons,
            start_date_time="2021-09-02T00:00:00Z",
            end_date_time="2021-09-06T23:59:59Z",
            date_time_field="date_time_field"
        )
        self.assertEqual(1.25, only_weekdays)
        all_week_combined = calculate_timespent_as_hours(
            self.one_week_of_noons,
            start_date_time="2021-09-01T00:00:00Z",
            end_date_time="2021-09-07T23:59:59Z",
            date_time_field="date_time_field",
            minutes=24 * 60
        )
        self.assertEqual(144.0, all_week_combined)
        just_one_hour = calculate_timespent_as_hours(
            self.every_ten_minutes_for_the_1st_hour_of_september_1st,
            date_time_field="date_time_field"
        )
        self.assertEqual(1.0, just_one_hour)

    def test_unique_days_worked(self):
        seven_unique_days = unique_days_worked(
            self.one_week_of_noons,
            start_date_time="2021-09-01T00:00:00Z",
            end_date_time="2021-09-07T23:59:59Z",
            date_time_field="date_time_field"
        )
        self.assertEqual(len(seven_unique_days), 7)
        weekdays = unique_days_worked(
            self.one_week_of_noons,
            start_date_time="2021-09-02T00:00:00Z",
            end_date_time="2021-09-06T23:59:59Z",
            date_time_field="date_time_field"
        )
        self.assertEqual(5, len(weekdays))

