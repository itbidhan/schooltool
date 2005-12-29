#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2005 Shuttleworth Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
Unit tests for schooltool.attendance.

$Id$
"""
__docformat__ = 'reStructuredText'


import unittest
import datetime

from persistent import Persistent
from zope.interface import implements
from zope.interface.verify import verifyObject
from zope.testing import doctest
from zope.app.testing import setup
from zope.app.annotation.interfaces import IAnnotations
from zope.app.annotation.interfaces import IAttributeAnnotatable
import zope.component

import schooltool.app # Dead chicken to appease the circle of import gods
from schooltool.person.interfaces import IPerson
from schooltool.calendar.interfaces import ICalendarEvent
from schooltool.attendance.interfaces import IDayAttendance
from schooltool.attendance.interfaces import IDayAttendanceRecord
from schooltool.attendance.interfaces import ISectionAttendance
from schooltool.attendance.interfaces import ISectionAttendanceRecord
from schooltool.attendance.interfaces import UNKNOWN, PRESENT, ABSENT, TARDY
from schooltool.attendance.interfaces import AttendanceError


#
# Stubs
#

class PersonStub(object):
    implements(IPerson, IAttributeAnnotatable)


class SectionStub(object):

    def __init__(self, title=None):
        self.title = title

    def __repr__(self):
        if self.title:
            return 'SectionStub(%r)' % self.title
        else:
            return 'SectionStub()'


class AttendanceRecordStub(object):

    def __init__(self, date, status):
        self.date = date
        self.status = status

    def isTardy(self):
        return self.status == TARDY

    def isAbsent(self):
        return self.status == ABSENT


#
# Attendance record classes
#

def doctest_AttendanceRecord_isUnknown_isPresent_isAbsent_isTardy():
    r"""Tests for SectionAttendanceRecord.isSomething functions

        >>> from schooltool.attendance.attendance import AttendanceRecord

        >>> for status in (UNKNOWN, PRESENT, ABSENT, TARDY):
        ...     ar = AttendanceRecord(status)
        ...     print "%-7s %-5s %-5s %-5s %-5s" % (ar.status,
        ...                 ar.isUnknown(), ar.isPresent(), ar.isAbsent(),
        ...                 ar.isTardy())
        UNKNOWN True  False False False
        PRESENT False True  False False
        ABSENT  False False True  False
        TARDY   False False False True

    """


def doctest_AttendanceRecord_makeTardy():
    r"""Tests for AttendanceRecord.makeTardy

        >>> from schooltool.attendance.attendance import AttendanceRecord

    If you have an absence

        >>> ar = AttendanceRecord(ABSENT)

    you can convert it to a tardy

        >>> ar.makeTardy(datetime.datetime(2005, 12, 16, 15, 03))

        >>> ar.isTardy()
        True
        >>> ar.late_arrival
        datetime.datetime(2005, 12, 16, 15, 3)

    In all other cases you can't.

        >>> for status in (UNKNOWN, PRESENT, TARDY):
        ...     ar = AttendanceRecord(status)
        ...     try:
        ...         ar.makeTardy(datetime.datetime(2005, 12, 16, 15, 03))
        ...     except AttendanceError:
        ...         pass
        ...     else:
        ...         print "no AttendanceError when status=%s" % status

    """


def doctest_AttendanceRecord_isExplained_addExplanation():
    r"""Tests for AttendanceRecord.addExplanation

        >>> from schooltool.attendance.attendance import AttendanceRecord

    If you have an absence

        >>> ar = AttendanceRecord(ABSENT)

    In the beginning it is not explained:

        >>> ar.isExplained()
        False

    You can add an explanation to it:

        >>> expn = ar.addExplanation("Was ill")
        >>> len(ar.explanations)
        1

    Having explanations in itself does not make the absence explained:

        >>> ar.isExplained()
        False

    However, if at least one the explanation is accepted, the absence
    is explained:

        >>> expn.accept()
        >>> ar.isExplained()
        True

    There even can be unaccepted and rejected explanations:

        >>> ar.addExplanation("Dog ate homework").reject()
        >>> expn2 = ar.addExplanation("Solar eclipse")
        >>> len(ar.explanations)
        3

    The absence is still explained:

        >>> ar.isExplained()
        True

    If the record's status is not ABSENT or TARDY, isExplained raises
    an exception:

        >>> ar.status = UNKNOWN
        >>> ar.isExplained()
        Traceback (most recent call last):
          ...
        AttendanceError: only absences and tardies can be explained.

        >>> ar.status = PRESENT
        >>> ar.isExplained()
        Traceback (most recent call last):
          ...
        AttendanceError: only absences and tardies can be explained.

        >>> ar.status = TARDY
        >>> ar.isExplained()
        True

    Likewise for addExplanation, it is only legal for absences and tardies:

        >>> ar.status = UNKNOWN
        >>> ar.addExplanation("whatever")
        Traceback (most recent call last):
          ...
        AttendanceError: only absences and tardies can be explained.

        >>> ar.status = PRESENT
        >>> ar.addExplanation("whatever")
        Traceback (most recent call last):
          ...
        AttendanceError: only absences and tardies can be explained.

        >>> ar.status = TARDY
        >>> ar.addExplanation("whatever")
        <schooltool.attendance.attendance.AbsenceExplanation object at ...>


    """


def doctest_AbsenceExplanation():
    """Absence explanation is a text with a status

        >>> from schooltool.attendance.attendance import AbsenceExplanation
        >>> from schooltool.attendance.interfaces import IAbsenceExplanation
        >>> expn = AbsenceExplanation("My dog ate my pants")
        >>> verifyObject(IAbsenceExplanation, expn)
        True

        >>> expn.text
        'My dog ate my pants'

    First the explanation is not accepted:

        >>> expn.isAccepted()
        False

        >>> expn.status
        'NEW'

    We can accept it:

        >>> expn.accept()
        >>> expn.status
        'ACCEPTED'
        >>> expn.isAccepted()
        True

    We can reject it:

        >>> expn.reject()
        >>> expn.status
        'REJECTED'
        >>> expn.isAccepted()
        False

    """


def doctest_DayAttendanceRecord():
    r"""Tests for DayAttendanceRecord

        >>> from schooltool.attendance.attendance \
        ...     import DayAttendanceRecord

    Let's create an UNKNOWN record

        >>> day = datetime.date(2005, 11, 23)
        >>> ar = DayAttendanceRecord(day, UNKNOWN)
        >>> verifyObject(IDayAttendanceRecord, ar)
        True

        >>> isinstance(ar, Persistent)
        True

        >>> ar.status == UNKNOWN
        True
        >>> ar.date == day
        True

        >>> ar.late_arrival is None
        True
        >>> ar.explanations
        []

    Let's create a regular record

        >>> day = datetime.date(2005, 11, 30)
        >>> ar = DayAttendanceRecord(day, ABSENT)
        >>> verifyObject(IDayAttendanceRecord, ar)
        True

        >>> ar.status == ABSENT
        True
        >>> ar.date == day
        True

        >>> ar.late_arrival is None
        True
        >>> ar.explanations
        []

    """


def doctest_SectionAttendanceRecord():
    r"""Tests for SectionAttendanceRecord

        >>> from schooltool.attendance.attendance \
        ...     import SectionAttendanceRecord

    Let's create an UNKNOWN record

        >>> section = SectionStub()
        >>> dt = datetime.datetime(2005, 11, 23, 14, 55)
        >>> ar = SectionAttendanceRecord(section, dt, UNKNOWN)
        >>> verifyObject(ISectionAttendanceRecord, ar)
        True

        >>> isinstance(ar, Persistent)
        True

        >>> ar.status == UNKNOWN
        True
        >>> ar.section == section
        True
        >>> ar.datetime == dt
        True
        >>> ar.date == dt.date()
        True

        >>> ar.duration
        datetime.timedelta(0)
        >>> ar.period_id is None
        True
        >>> ar.late_arrival is None
        True
        >>> ar.explanations
        []

    Let's create a regular record

        >>> section = SectionStub()
        >>> dt = datetime.datetime(2005, 11, 23, 14, 55)
        >>> duration = datetime.timedelta(minutes=45)
        >>> period_id = 'Period A'
        >>> ar = SectionAttendanceRecord(section, dt, PRESENT, duration,
        ...                              period_id)

        >>> ar.status == PRESENT
        True
        >>> ar.section == section
        True
        >>> ar.datetime == dt
        True
        >>> ar.date == dt.date()
        True
        >>> ar.duration == duration
        True
        >>> ar.period_id == period_id
        True

        >>> ar.late_arrival is None
        True
        >>> ar.explanations
        []

    """


#
# Attendance storage classes
#

def doctest_AttendanceFilteringMixin_filter():
    r"""Tests for AttendanceFilteringMixin.filter

        >>> d1 = datetime.date(2005, 12, 5)
        >>> d2 = datetime.date(2005, 12, 7)
        >>> d3 = datetime.date(2005, 12, 9)

        >>> from schooltool.attendance.attendance \
        ...         import AttendanceFilteringMixin
        >>> from schooltool.attendance.attendance import DayAttendanceRecord
        >>> class AttendanceStub(AttendanceFilteringMixin):
        ...     def __iter__(self):
        ...         yield DayAttendanceRecord(d1, PRESENT)
        ...         yield DayAttendanceRecord(d2, PRESENT)
        ...         yield DayAttendanceRecord(d2, ABSENT)
        ...         yield DayAttendanceRecord(d3, PRESENT)
        >>> attendance = AttendanceStub()

        >>> def print_for(first, last):
        ...     for r in attendance.filter(first, last):
        ...         print r.date, r.isPresent()

        >>> print_for(d1, d1)
        2005-12-05 True

        >>> print_for(d1, d2)
        2005-12-05 True
        2005-12-07 True
        2005-12-07 False

        >>> print_for(d2, d3)
        2005-12-07 True
        2005-12-07 False
        2005-12-09 True

        >>> print_for(d1, d3)
        2005-12-05 True
        2005-12-07 True
        2005-12-07 False
        2005-12-09 True

        >>> print_for(d3, d1)

    """


def doctest_AttendanceCalendarMixin_makeCalendar():
    r"""Tests for AttendanceCalendarMixin.makeCalendar

        >>> from schooltool.attendance.attendance \
        ...         import AttendanceCalendarMixin
        >>> acm = AttendanceCalendarMixin()

    When there are no incidents stored, makeCalendar returns an empty
    ImmutableCalendar:

        >>> acm.filter = lambda first, last: []
        >>> cal = acm.makeCalendar(datetime.date(2005, 12, 5),
        ...                        datetime.date(2005, 12, 6))
        >>> cal
        <schooltool.calendar.simple.ImmutableCalendar object at ...>
        >>> list(cal)
        []

    Let's add some incidents:

        >>> dt1a = datetime.datetime(2005, 12, 5, 13, 30)
        >>> dt1b = datetime.datetime(2005, 12, 5, 15, 30)
        >>> dt2a = datetime.datetime(2005, 12, 7, 13, 30)
        >>> dt2b = datetime.datetime(2005, 12, 7, 15, 30)
        >>> dt3a = datetime.datetime(2005, 12, 9, 13, 30)

        >>> r1 = AttendanceRecordStub(dt1a, PRESENT)
        >>> r2 = AttendanceRecordStub(dt2a, PRESENT)
        >>> r3 = AttendanceRecordStub(dt2a, ABSENT)
        >>> r4 = AttendanceRecordStub(dt2b, TARDY)
        >>> r5 = AttendanceRecordStub(dt3a, PRESENT)

        >>> from schooltool.calendar.simple import SimpleCalendarEvent
        >>> acm.filter = lambda first, last: [r1, r2, r3, r4, r5]
        >>> acm.absenceEventTitle = lambda record: 'Was absent'
        >>> acm.tardyEventTitle = lambda record: 'Was late'
        >>> acm.makeCalendarEvent = lambda r, title: SimpleCalendarEvent(
        ...                             r.date, datetime.timedelta(0), title)

    Now let's inspect the calendar produced for the second day:

        >>> def print_for(first, last):
        ...     def key(event):
        ...         return (event.dtstart, event.title)
        ...     for ev in sorted(acm.makeCalendar(first, last), key=key):
        ...         print ev.dtstart, ev.title

        >>> print_for(dt1a.date(), dt3a.date())
        2005-12-07 13:30:00+00:00 Was absent
        2005-12-07 15:30:00+00:00 Was late

    """


def doctest_DayAttendance():
    """Test for DayAttendance

        >>> from schooltool.attendance.attendance import DayAttendance
        >>> da = DayAttendance()
        >>> verifyObject(IDayAttendance, da)
        True

        >>> isinstance(da, Persistent)
        True

    """


def doctest_DayAttendance_record():
    """Test for DayAttendance.record

        >>> from schooltool.attendance.attendance import DayAttendance
        >>> da = DayAttendance()

        >>> len(list(da))
        0

    Let's record a presence

        >>> day = datetime.date(2005, 12, 9)
        >>> da.record(day, True)

    We can check that it is there

        >>> len(list(da))
        1

        >>> ar = da.get(day)
        >>> ar
        DayAttendanceRecord(datetime.date(2005, 12, 9), PRESENT)
        >>> IDayAttendanceRecord.providedBy(ar)
        True

    It has all the data

        >>> ar.date == day
        True
        >>> ar.status == PRESENT
        True

    Let's record an absence

        >>> day2 = datetime.date(2005, 12, 7)
        >>> da.record(day2, False)

    We can check that it is there

        >>> len(list(da))
        2

        >>> ar = da.get(day2)
        >>> ar.date == day2
        True
        >>> ar.status == ABSENT
        True

    We cannot override existing records

        >>> da.record(day, False)
        Traceback (most recent call last):
          ...
        AttendanceError: record for 2005-12-09 already exists

        >>> da.record(day, True)
        Traceback (most recent call last):
          ...
        AttendanceError: record for 2005-12-09 already exists

        >>> da.record(day2, False)
        Traceback (most recent call last):
          ...
        AttendanceError: record for 2005-12-07 already exists

    """


def doctest_DayAttendance_get():
    """Tests for DayAttendance.get

        >>> from schooltool.attendance.attendance import DayAttendance
        >>> da = DayAttendance()

    If you try to see the attendance record that has never been recorded, you
    get a "null object".

        >>> day = datetime.date(2005, 12, 3)
        >>> ar = da.get(day)
        >>> ar
        DayAttendanceRecord(datetime.date(2005, 12, 3), UNKNOWN)
        >>> IDayAttendanceRecord.providedBy(ar)
        True
        >>> ar.status == UNKNOWN
        True
        >>> ar.date == day
        True

    Otherwise you get the correct record for a given date

        >>> day1 = datetime.date(2005, 12, 9)
        >>> day2 = datetime.date(2005, 12, 10)
        >>> da.record(day1, True)
        >>> da.record(day2, False)

        >>> for day in (day1, day2):
        ...     ar = da.get(day)
        ...     assert ar.date == day
        ...     print ar.date, ar.isPresent()
        2005-12-09 True
        2005-12-10 False

    """


def doctest_DayAttendance_iter():
    """Tests for DayAttendance.__iter__

        >>> from schooltool.attendance.attendance import DayAttendance
        >>> da = DayAttendance()

        >>> list(da)
        []

        >>> day1 = datetime.date(2005, 12, 9)
        >>> da.record(day1, True)

        >>> list(da)
        [DayAttendanceRecord(datetime.date(2005, 12, 9), PRESENT)]

        >>> day2 = datetime.date(2005, 12, 10)
        >>> da.record(day2, False)

        >>> list(da)
        [DayAttendanceRecord(...), DayAttendanceRecord(...)]
        >>> sorted(ar.date for ar in da)
        [datetime.date(2005, 12, 9), datetime.date(2005, 12, 10)]

    """


def doctest_DayAttendance_tardyEventTitle():
    r"""Tests for DayAttendance.tardyEventTitle

        >>> from schooltool.attendance.attendance import DayAttendance
        >>> from schooltool.attendance.attendance import DayAttendanceRecord
        >>> sa = DayAttendance()

        >>> day = datetime.date(2005, 11, 23)
        >>> ar = DayAttendanceRecord(day, ABSENT)
        >>> ar.makeTardy(datetime.datetime(2005, 11, 23, 17, 32))

        >>> print sa.tardyEventTitle(ar)
        Was late for homeroom.

    """


def doctest_DayAttendance_absenceEventTitle():
    r"""Tests for DayAttendance.absenceEventTitle

        >>> from schooltool.attendance.attendance import DayAttendance
        >>> from schooltool.attendance.attendance import DayAttendanceRecord
        >>> sa = DayAttendance()

        >>> day = datetime.date(2005, 11, 23)
        >>> ar = DayAttendanceRecord(day, ABSENT)

        >>> print sa.absenceEventTitle(ar)
        Was absent from homeroom.

    """


def doctest_DayAttendance_makeCalendarEvent():
    r"""Tests for DayAttendance.makeCalendarEvent

        >>> from schooltool.attendance.attendance import DayAttendance
        >>> from schooltool.attendance.attendance import DayAttendanceRecord
        >>> sa = DayAttendance()

        >>> day = datetime.date(2005, 11, 23)
        >>> ar = DayAttendanceRecord(day, ABSENT)

        >>> ev = sa.makeCalendarEvent(ar, 'John was bad today')
        >>> ICalendarEvent.providedBy(ev)
        True
        >>> ev.allday
        True
        >>> print ev.dtstart, ev.duration, ev.title
        2005-11-23 00:00:00+00:00 1 day, 0:00:00 John was bad today

    """


def doctest_SectionAttendance():
    """Test for SectionAttendance

        >>> from schooltool.attendance.attendance import SectionAttendance
        >>> sa = SectionAttendance()
        >>> verifyObject(ISectionAttendance, sa)
        True

        >>> isinstance(sa, Persistent)
        True

    """


def doctest_SectionAttendance_record():
    """Tests for SectionAttendance.record

        >>> from schooltool.attendance.attendance import SectionAttendance
        >>> sa = SectionAttendance()

        >>> len(list(sa))
        0

    Let's record a presence

        >>> section = SectionStub()
        >>> dt = datetime.datetime(2005, 12, 9, 13, 30)
        >>> duration = datetime.timedelta(minutes=45)
        >>> period_id = 'P1'
        >>> sa.record(section, dt, duration, period_id, True)

    We can check that it is there

        >>> len(list(sa))
        1

        >>> ar = sa.get(section, dt)
        >>> ar
        SectionAttendanceRecord(SectionStub(),
                                datetime.datetime(2005, 12, 9, 13, 30),
                                PRESENT)
        >>> ISectionAttendanceRecord.providedBy(ar)
        True

    It has all the data

        >>> ar.section is section
        True
        >>> ar.datetime == dt
        True
        >>> ar.duration == duration
        True
        >>> ar.period_id == period_id
        True
        >>> ar.status == PRESENT
        True

    Let's record an absence for the same section

        >>> dt = datetime.datetime(2005, 12, 9, 14, 30)
        >>> duration = datetime.timedelta(minutes=30)
        >>> period_id = 'P2'
        >>> sa.record(section, dt, duration, period_id, False)

    We can check that it is there

        >>> len(list(sa))
        2

        >>> ar = sa.get(section, dt)
        >>> ar.section is section
        True
        >>> ar.datetime == dt
        True
        >>> ar.duration == duration
        True
        >>> ar.period_id == period_id
        True
        >>> ar.status == ABSENT
        True

    Let's record a presence for another section at the same time

        >>> section2 = SectionStub()
        >>> sa.record(section2, dt, duration, period_id, True)

        >>> len(list(sa))
        3

        >>> ar = sa.get(section2, dt)
        >>> ar.section is section2
        True

    However we cannot override existing records

        >>> sa.record(section2, dt, duration, period_id, True)
        Traceback (most recent call last):
          ...
        AttendanceError: record for SectionStub() at 2005-12-09 14:30:00
                         already exists

    """


def doctest_SectionAttendance_get():
    """Tests for SectionAttendance.get

        >>> from schooltool.attendance.attendance import SectionAttendance
        >>> sa = SectionAttendance()

        >>> section1 = SectionStub()
        >>> section2 = SectionStub()
        >>> dt = datetime.datetime(2005, 12, 9, 13, 30)

    If you try to see the attendance record that has never been recorded, you
    get a "null object".

        >>> ar = sa.get(section1, dt)
        >>> ar
        SectionAttendanceRecord(SectionStub(),
                                datetime.datetime(2005, 12, 9, 13, 30),
                                UNKNOWN)
        >>> ISectionAttendanceRecord.providedBy(ar)
        True
        >>> ar.status == UNKNOWN
        True
        >>> ar.section == section1
        True
        >>> ar.datetime == dt
        True

    Most of the attributes do not make much sense

        >>> ar.duration
        datetime.timedelta(0)
        >>> ar.period_id

    Otherwise you get the correct record for a (section, datetime) pair.

        >>> dt1 = datetime.datetime(2005, 12, 9, 13, 30)
        >>> dt2 = datetime.datetime(2005, 12, 10, 13, 0)
        >>> duration = datetime.timedelta(minutes=50)
        >>> sa.record(section1, dt1, duration, 'P1', True)
        >>> sa.record(section2, dt1, duration, 'P2', False)
        >>> sa.record(section1, dt2, duration, 'P3', False)
        >>> sa.record(section2, dt2, duration, 'P4', True)

        >>> for dt in (dt1, dt2):
        ...     for section in (section1, section2):
        ...         ar = sa.get(section, dt)
        ...         assert ar.section == section
        ...         assert ar.datetime == dt
        ...         print ar.period_id, ar.isPresent()
        P1 True
        P2 False
        P3 False
        P4 True

    """


def doctest_SectionAttendance_getAllForDay():
    """Tests for SectionAttendance.getAllForDay

        >>> from schooltool.attendance.attendance import SectionAttendance
        >>> sa = SectionAttendance()

        >>> section1 = SectionStub('Math')
        >>> section2 = SectionStub('Chem')
        >>> dt1a = datetime.datetime(2005, 12, 5, 13, 30)
        >>> dt1b = datetime.datetime(2005, 12, 5, 15, 30)
        >>> dt2a = datetime.datetime(2005, 12, 7, 13, 30)
        >>> dt2b = datetime.datetime(2005, 12, 7, 15, 30)
        >>> dt3a = datetime.datetime(2005, 12, 9, 13, 30)
        >>> dt3b = datetime.datetime(2005, 12, 9, 15, 30)
        >>> duration = datetime.timedelta(minutes=45)

        >>> sa.record(section1, dt1a, duration, 'A', True)
        >>> sa.record(section1, dt2a, duration, 'A', True)
        >>> sa.record(section2, dt2a, duration, 'A', False)
        >>> sa.record(section1, dt2b, duration, 'B', False)
        >>> sa.record(section2, dt3a, duration, 'A', True)

        >>> def print_for(day):
        ...     def key(ar):
        ...         return (ar.datetime, ar.section.title)
        ...     for ar in sorted(sa.getAllForDay(day), key=key):
        ...         print ar.date, ar.period_id, ar.section.title, ar.isPresent()

        >>> print_for(dt1a.date())
        2005-12-05 A Math True

        >>> print_for(dt2a.date())
        2005-12-07 A Chem False
        2005-12-07 A Math True
        2005-12-07 B Math False

        >>> print_for(dt3a.date())
        2005-12-09 A Chem True

        >>> print_for(datetime.date(2005, 12, 4))

    """


def doctest_SectionAttendance_tardyEventTitle():
    r"""Tests for SectionAttendance.tardyEventTitle

        >>> from schooltool.attendance.attendance import SectionAttendance
        >>> from schooltool.attendance.attendance \
        ...     import SectionAttendanceRecord
        >>> sa = SectionAttendance()

        >>> section = SectionStub(title="Lithomancy")
        >>> dt = datetime.datetime(2005, 11, 23, 14, 55)
        >>> duration = datetime.timedelta(minutes=45)
        >>> period_id = 'Period A'
        >>> ar = SectionAttendanceRecord(section, dt, ABSENT, duration,
        ...                              period_id)
        >>> minutes_late = 14
        >>> ar.makeTardy(dt + datetime.timedelta(minutes=minutes_late))

        >>> print sa.tardyEventTitle(ar)
        Was late for Lithomancy (14 minutes).

    """


def doctest_SectionAttendance_absenceEventTitle():
    r"""Tests for SectionAttendance.absenceEventTitle

        >>> from schooltool.attendance.attendance import SectionAttendance
        >>> from schooltool.attendance.attendance \
        ...     import SectionAttendanceRecord
        >>> sa = SectionAttendance()

        >>> section = SectionStub(title="Lithomancy")
        >>> dt = datetime.datetime(2005, 11, 23, 14, 55)
        >>> duration = datetime.timedelta(minutes=45)
        >>> period_id = 'Period A'
        >>> ar = SectionAttendanceRecord(section, dt, ABSENT, duration,
        ...                              period_id)

        >>> print sa.absenceEventTitle(ar)
        Was absent from Lithomancy.

    """


def doctest_SectionAttendance_makeCalendarEvent():
    r"""Tests for SectionAttendance.makeCalendarEvent

        >>> from schooltool.attendance.attendance import SectionAttendance
        >>> from schooltool.attendance.attendance \
        ...     import SectionAttendanceRecord
        >>> sa = SectionAttendance()

        >>> section = SectionStub()
        >>> dt = datetime.datetime(2005, 11, 23, 14, 55)
        >>> duration = datetime.timedelta(minutes=45)
        >>> period_id = 'Period A'
        >>> ar = SectionAttendanceRecord(section, dt, ABSENT, duration,
        ...                              period_id)

        >>> ev = sa.makeCalendarEvent(ar, 'John was bad today')
        >>> ICalendarEvent.providedBy(ev)
        True
        >>> print ev.dtstart, ev.duration, ev.title
        2005-11-23 14:55:00+00:00 0:45:00 John was bad today

    """


#
# Adapters
#

def doctest_getSectionAttendance():
    """Tests for getSectionAttendance.

        >>> setup.placelessSetUp()
        >>> setup.setUpAnnotations()
        >>> from schooltool.attendance.attendance import getSectionAttendance
        >>> zope.component.provideAdapter(getSectionAttendance,
        ...                               [IPerson], ISectionAttendance)

    getSectionAttendance lets us get ISectionAttendance for a person

        >>> person = PersonStub()
        >>> attendance = ISectionAttendance(person)
        >>> attendance
        <schooltool.attendance.attendance.SectionAttendance object at ...>

    The attendance object is stored in person's annotations

        >>> annotations = IAnnotations(person)
        >>> attendance is annotations['schooltool.attendance.SectionAttendance']
        True

    If you adapt more than once, you will get the same object

        >>> attendance is ISectionAttendance(person)
        True

        >>> setup.placelessTearDown()

    """


def doctest_getDayAttendance():
    """Tests for getDayAttendance.

        >>> setup.placelessSetUp()
        >>> setup.setUpAnnotations()
        >>> from schooltool.attendance.attendance import getDayAttendance
        >>> zope.component.provideAdapter(getDayAttendance,
        ...                               [IPerson], IDayAttendance)

    getDayAttendance lets us get IDayAttendance for a person

        >>> person = PersonStub()
        >>> attendance = IDayAttendance(person)
        >>> attendance
        <schooltool.attendance.attendance.DayAttendance object at ...>

    The attendance object is stored in person's annotations

        >>> annotations = IAnnotations(person)
        >>> attendance is annotations['schooltool.attendance.DayAttendance']
        True

    If you adapt more than once, you will get the same object

        >>> attendance is IDayAttendance(person)
        True

        >>> setup.placelessTearDown()

    """


def test_suite():
    optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return doctest.DocTestSuite(optionflags=optionflags)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')