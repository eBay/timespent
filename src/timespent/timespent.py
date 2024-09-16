import datetime
from abc import abstractmethod
from typing import List, Optional, Dict

from clientwrapper import BasicMapping

DateTime = datetime.datetime
Date = datetime.date
TimeDelta = datetime.timedelta
strptime = datetime.datetime.strptime
strftime = datetime.datetime.strftime


class Event(BasicMapping):
    def __init__(self, date_str: str, date_time_field: str, date_time_format: str):
        data = {date_time_field: date_str}
        super().__init__(data)
        self.date_time_format = date_time_format
        self.date_time_field = date_time_field
        self.date_time_str = self.data[date_time_field]
        self.date_time = strptime(self.date_time_str, self.date_time_format)

    def __repr__(self):
        return str(self.data)

    @property
    def date(self):
        return self.date_time.date()


class BasicSession(BasicMapping):
    def __init__(self, events: List[Dict[str, str]], date_time_field: str, date_time_format: str,
                 minutes_buffer: int = 15):
        super().__init__(dict())
        self.date_time_field = date_time_field
        self.date_time_format = date_time_format
        self.minutes_buffer = minutes_buffer
        self._time_spent_: TimeDelta = TimeDelta(minutes=0)
        self._events_: List[Event] = list(map(lambda e: Event(
            date_str=e[date_time_field],
            date_time_field=date_time_field,
            date_time_format=date_time_format
        ), events))
        self.data = self.dict()

    @property
    def events(self) -> List[Event]:
        self._events_.sort(key=lambda e: e[self.date_time_field])
        return self._events_

    @property
    def start_date_time(self) -> DateTime:
        return strptime(self.events[0][self.date_time_field], self.date_time_format)

    @property
    def stop_date_time(self) -> DateTime:
        return strptime(self.events[-1][self.date_time_field], self.date_time_format)

    @property
    def start_date(self) -> Date:
        return self.start_date_time.date()

    @property
    def stop_date(self) -> Date:
        return self.stop_date_time.date()

    def dict(self, **kwargs) -> Dict[str, str]:
        summary = {
            "start_time": strftime(self.start_date_time, self.date_time_format),
            "stop_time": strftime(self.stop_date_time, self.date_time_format),
            "time_spent": str(self.time_spent_as_hours),
        }
        summary.update(kwargs)
        return summary

    def __str__(self):
        return str(self.dict())

    @property
    @abstractmethod
    def time_spent(self) -> TimeDelta:
        pass

    @property
    def time_spent_as_hours(self) -> float:
        return round(self.time_spent.total_seconds() / 3600, 2)


class WorkSession(BasicSession):
    def __init__(self, events: List[Dict], date_time_field: str, date_time_format: str, minutes_buffer: int = 15):
        super().__init__(events, date_time_field, date_time_format, minutes_buffer)

    @property
    def time_spent(self) -> TimeDelta:
        window = self.stop_date_time - self.start_date_time
        before_event_buffer = TimeDelta(minutes=self.minutes_buffer)
        if window > TimeDelta(minutes=self.minutes_buffer):
            return window
        return before_event_buffer


def map_dicts_to_work_sessions(
        events: List[Dict[str, str]],
        date_time_field: str = "date_time",
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        **kwargs
) -> List[WorkSession]:
    date_time_format: str = kwargs.get('date_time_format', '%Y-%m-%dT%H:%M:%SZ')
    minutes: int = kwargs.get('minutes', 15)
    if start_date_time is not None and end_date_time is not None:
        start_date_time = strptime(start_date_time, date_time_format)
        end_date_time = strptime(end_date_time, date_time_format)
        events = filter(lambda e: start_date_time < strptime(e[date_time_field], date_time_format) < end_date_time,
                        events)
    elif start_date_time:
        start_date_time = strptime(start_date_time, date_time_format)
        events = filter(lambda e: strptime(e[date_time_field], date_time_format) > start_date_time, events)
    elif end_date_time:
        end_date_time = strptime(end_date_time, date_time_format)
        events = filter(lambda e: strptime(e[date_time_field], date_time_format) < end_date_time, events)
    sorted_events: List[Dict[str, str]] = sorted(events, key=lambda e: e[date_time_field])
    work_events: List[Dict[str, str]] = []
    work_sessions: List[WorkSession] = []
    index = 0
    while index < len(sorted_events):
        work_event = sorted_events[index]
        index += 1
        if len(work_events) == 0:
            work_events.append(work_event)
        else:
            last_event = work_events[-1]
            if too_long_after_last_event(strptime(last_event[date_time_field], date_time_format),
                                         strptime(work_event[date_time_field], date_time_format), minutes):
                work_sessions.append(WorkSession(work_events, date_time_field, date_time_format, minutes))
                work_events = []
            work_events.append(work_event)
        if index == len(sorted_events):
            work_sessions.append(WorkSession(work_events, date_time_field, date_time_format, minutes))
    return work_sessions


def calculate_timespent(
        events: List[Dict[str, str]],
        date_time_field: str = "date_time",
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        **kwargs
) -> TimeDelta:
    work_sessions = map_dicts_to_work_sessions(events, date_time_field, start_date_time, end_date_time, **kwargs)
    time_spent = TimeDelta(minutes=0)
    for work_session in work_sessions:
        time_spent += work_session.time_spent
    return time_spent


def calculate_timespent_as_hours(
        events: List[Dict[str, str]],
        date_time_field: str = "date_time",
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        **kwargs
) -> float:
    time_spent = calculate_timespent(events, date_time_field, start_date_time, end_date_time, **kwargs)
    return round(time_spent.total_seconds() / 3600, 2)


def unique_days_worked(
        events: List[Dict[str, str]],
        date_time_field: str = "date_time",
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        **kwargs
) -> List[Date]:
    work_sessions = map_dicts_to_work_sessions(events, date_time_field, start_date_time, end_date_time, **kwargs)
    udw = []
    for work_session in work_sessions:
        udw.extend([work_session.start_date, work_session.stop_date])
    return list(set(udw))


def too_long_after_last_event(last_event: DateTime, new_event: DateTime, minutes_buffer: int) -> bool:
    how_long_since_last_event = new_event - last_event
    buffer = TimeDelta(minutes=minutes_buffer)
    return how_long_since_last_event > buffer
