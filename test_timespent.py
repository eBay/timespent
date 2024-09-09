import unittest
from datetime import datetime


from timespent import FilterType, Filter


class MyTestCase(unittest.TestCase):
    def test_filter(self):
        dt = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%SZ")
        test_filter = Filter("author", "email", dt, FilterType.COMMIT)
        self.assertEqual(test_filter.author_name, "author")
        self.assertEqual(test_filter.author_email, "email")
        self.assertEqual(test_filter.date_time_str, dt)
        self.assertEqual(test_filter.category, FilterType.COMMIT)
