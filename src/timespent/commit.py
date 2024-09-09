import collections.abc as abc
from datetime import datetime
from enum import Enum


class FilterType(Enum):
    REPO = "REPO"
    COMMIT = "COMMIT"
    COMMENT = "COMMENT"
    PR = "PR"
    AUTHOR = "AUTHOR"


class Filter(abc.Mapping):
    def __init__(self, author_name: str, author_email: str, remove_author_names: list[str], date_time_str: str, category: FilterType):
        self.bot_names = remove_author_names
        self.date_time_str = date_time_str
        self.date_time = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%SZ")
        self.category = category
        self.author_name = author_name
        self.author_email = author_email

    def dict(self):
        return {
            "author_name": self.author_name,
            "author_email": self.author_email,
            "date_time": self.date_time_str,
            "type": self.category
        }

    def is_author_bot(self):
        return any([bot_name in self.author_name for bot_name in self.bot_names])

    def is_author(self, author_names: list):
        return any([author_name in self.author_name for author_name in author_names])

    def is_after(self, end_date_time_str: str):
        end_date_time = datetime.strptime(end_date_time_str, "%Y-%m-%dT%H:%M:%SZ")
        return self.date_time > end_date_time

    def is_before(self, start_date_time_str: str):
        start_date_time = datetime.strptime(start_date_time_str, "%Y-%m-%dT%H:%M:%SZ")
        return self.date_time < start_date_time

    def is_between(self, start_date_time_str: str, end_date_time_str: str):
        return self.is_after(start_date_time_str) and self.is_before(end_date_time_str)

    def __str__(self):
        return str(self.dict())

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        return iter(self.dict())

    def __len__(self):
        return len(self.dict())


class CommitFilter(Filter):
    def __init__(self, raw_data, remove_author_names: list[str], **kwargs):
        kwargs['message'] = raw_data.get('message', '')
        kwargs['sha'] = raw_data.get('sha', '')
        raw_data_author = raw_data.get('commit', dict()).get('author', dict())
        date_time = raw_data_author.get('date', '')
        super().__init__('', '', remove_author_names=remove_author_names, date_time_str=date_time, category=FilterType.COMMIT)
        self.__dict__.update(kwargs)

    def __repr__(self):
        return str(self.dict())


class CommentFilter(Filter):
    def __init__(self, raw_data: dict[str, str], remove_author_names: list[str], **kwargs):
        kwargs['body'] = raw_data.get('body', '')
        kwargs['commit_id'] = raw_data.get('commit_id', '')
        date_time = raw_data.get('created_at', '')
        category = FilterType.COMMENT
        super().__init__('', '', remove_author_names=remove_author_names, date_time_str=date_time, category=category)
        self.__dict__.update(kwargs)
