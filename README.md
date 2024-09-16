# timespent (licensed under Apache 2.0)
Python package for calculating time spent in any list of dict with date/time fields.

Key Features:
- WorkSession: class for representing a span of time. Can be saved in pandas DataFrame.
- map_dicts_to_work_sessions: maps list of dict to WorkSession objects for duration calculation.
- calculate_timespent: calculates total time spent in a list of WorkSession objects.
- calculate_timespent_as_hours: calculates total time spent in a list of WorkSession objects in hours (float).
- unique_days_worked: returns list of unique days worked.