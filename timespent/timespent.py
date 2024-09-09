import collections.abc
import datetime
import time

import pandas as pd
from clientwrapper import ClientWrapper


class DurationException(Exception):
    def __init__(self, message):
        self.message = message


class WorkSession(collections.abc.Mapping):
    def __init__(self, before_commit_buffer=10, between_commit_buffer=15):
        self._date_ = None
        self._start_time_ = None
        self._stop_time_ = None
        self._duration_ = datetime.timedelta(minutes=before_commit_buffer)
        self.full_time_format = '%Y-%m-%dT%H:%M:%SZ'
        self.ymd_time_format = '%Y-%m-%d'
        self.seconds_in_hour = 3600
        self.before_commit_buffer = before_commit_buffer
        self.between_commit_buffer = between_commit_buffer
        self._commits_ = []

    def dict(self):
        return {
            "date": self._date_,
            "start_time": self._start_time_,
            "stop_time": self._stop_time_,
            "hours": round(self.duration.seconds / self.seconds_in_hour, 2),
        }

    def __repr__(self):
        return str(self.dict())

    @property
    def commits(self):
        return self._commits_

    @property
    def date(self):
        return self._date_

    @date.setter
    def date(self, date_str):
        ymd_str = date_str.split('T')[0]
        self._date_ = datetime.datetime.strptime(ymd_str, self.ymd_time_format)
        self.start_time = date_str

    @property
    def start_time(self):
        return self._start_time_

    @start_time.setter
    def start_time(self, start_time):
        if self._start_time_ is not None:
            raise Exception("Start time already set")
        start_time_without_buffer = datetime.datetime.strptime(start_time, self.full_time_format)
        self._start_time_ = start_time_without_buffer - datetime.timedelta(minutes=self.before_commit_buffer)

    @property
    def stop_time(self):
        return self._stop_time_

    @stop_time.setter
    def stop_time(self, new_commit_str):
        new_commit = datetime.datetime.strptime(new_commit_str, self.full_time_format)
        previous_commit = self.start_time if self.stop_time is None else self.stop_time
        too_long = self.too_long_after_last_commit(previous_commit, new_commit)
        if too_long:
            self._stop_time_ = previous_commit
            raise DurationException("Too long after last commit")
        else:
            self._stop_time_ = new_commit

    @property
    def duration(self):
        window = self.stop_time - self.start_time
        before_commit_buffer = datetime.timedelta(minutes=self.before_commit_buffer)
        if window > datetime.timedelta(minutes=self.between_commit_buffer):
            return window
        return before_commit_buffer

    def too_long_after_last_commit(self, last_commit, new_commit):
        how_long_since_last_commit = new_commit - last_commit
        buffer = datetime.timedelta(minutes=self.between_commit_buffer)
        return how_long_since_last_commit > buffer

    def __str__(self):
        return str(self.dict())

    def __getitem__(self, key):
        return self.dict()[key]

    def __iter__(self):
        return iter(self.dict())

    def __len__(self):
        return len(self.dict())


class TimeSpent(ClientWrapper):
    def __init__(self):
        super().__init__()
        self.ps_data = []
        self.githubclient = None
        self.repo = None
        self.contributors = []
        self.include_comments = None
        self.start_date_time = None
        self.end_date_time = None
        self.all_milestones = []

    def _set_parameters_(self, repo, github_url, contributors=[], include_comments=True, start_date_time=None,
                         end_date_time=None):
        self.repo = repo.replace(github_url, '')
        self.contributors = contributors
        self.include_comments = include_comments
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time

    def _query_github_(self):
        self.githubclient.query_repos_by_name(self.repo)
        self.githubclient.query_all_commits()
        if self.include_comments:
            self.githubclient.query_all_repo_comments()
        all_commits = self.githubclient.get_commits()
        all_comments = self.githubclient.get_comments()
        self.all_milestones = all_commits + all_comments

    def _filter_milestones_(self):
        time_filtered_milestones = self._filter_by_time_(self.all_milestones)
        author_filtered_milestones = self._filter_by_author_(time_filtered_milestones)
        return list(author_filtered_milestones)

    def _filter_by_time_(self, milestones):
        filter_after = self.start_date_time is not None
        filter_before = self.end_date_time is not None
        if filter_after and filter_before:
            return filter(lambda milestone: milestone.is_between(self.start_date_time, self.end_date_time), milestones)
        elif filter_after:
            return filter(lambda milestone: milestone.is_after(self.start_date_time), milestones)
        elif filter_before:
            return filter(lambda milestone: milestone.is_before(self.end_date_time), milestones)
        else:
            return milestones

    def _filter_by_author_(self, milestones):
        if len(self.contributors) == 0:
            return milestones
        return filter(lambda milestone: milestone.is_author(self.contributors), milestones)

    def _collect_durations_(self):
        contributor_names = set(list(map(lambda x: x['author_name'], self.all_milestones)))
        contributor_names = [name for name in contributor_names if name != '']
        contributor_dicts = []
        filtered_milestones = self._filter_milestones_()
        for contributor_name in contributor_names:
            author_filtered_milestones = list(
                filter(lambda x: x['author_name'] == contributor_name, filtered_milestones))
            author_durations = []
            duration = WorkSession()
            index = 0
            sorted_milestones = sorted(author_filtered_milestones, key=lambda x: x['date_time'])
            while index < len(sorted_milestones):
                milestone = sorted_milestones[index]
                index += 1
                try:
                    if index == len(sorted_milestones) - 1:
                        author_durations += [duration]
                        last_duration = WorkSession()
                        last_duration.date = milestone.date_time_str
                        last_duration.stop_time = milestone.date_time_str
                        author_durations += [last_duration]
                    elif duration.date is None:
                        duration.date = milestone.date_time_str
                    else:
                        duration.stop_time = milestone.date_time_str
                except DurationException:
                    author_durations += [duration]
                    duration = WorkSession()
                    duration.date = milestone.date_time_str
            days_worked = []
            time_spent = datetime.timedelta(0, 0)
            for duration in author_durations:
                days_worked.append(duration.date)
                time_spent += duration.duration
            contributor_dict = {
                "repo": self.repo,
                "author": contributor_name,
                "days_worked": len(set(days_worked)),
                "time_spent": time_spent
            }
            contributor_dicts.append(contributor_dict)
        df = pd.DataFrame(contributor_dicts)
        df.to_csv("output-" + time.ctime() + ".csv", index=False)

    def get_timespent(
            self,
            github_url,
            repo,
            contributors=[],
            include_comments=True,
            start_date_time=None,
            end_date_time=None
    ):
        self._set_parameters_(
            repo=repo,
            github_url=github_url,
            contributors=contributors,
            include_comments=include_comments,
            start_date_time=start_date_time,
            end_date_time=end_date_time
        )
        self._query_github_()
        self._collect_durations_()
