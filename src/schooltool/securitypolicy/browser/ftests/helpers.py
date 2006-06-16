"""
Helper functions for functional tests.

$Id$
"""

def go_home(browser):
    browser.open('http://localhost/')


def person_container_view(browser, subject):
    go_home(browser)
    browser.getLink('Persons').click()
    if subject in browser.contents:
        return True

def person_container_edit(browser, subject):
    person_container_view(browser, subject)
    return browser.getControl('Delete')


def person_data_view(browser, subject):
    browser.open('http://localhost/persons/%s/' % subject)
    return subject in browser.contents

def person_data_edit(browser, subject):
    browser.open('http://localhost/persons/%s/@@edit.html' % subject)
    ctrl = browser.getControl('Preferred name')
    ctrl.value = ctrl.value + ' ook'
    browser.getControl('Apply', index=0).click()
    return 'Updated' in browser.contents


def person_calendar_view(browser, subject):
    browser.open('http://localhost/persons/%s/calendar' % subject)
    return 'Calendar for' in browser.contents

def person_calendar_edit(browser, subject):
    person_calendar_view(browser, subject)
    browser.getLink('9:00').click()
    browser.getControl('Title').value = 'Test event'
    browser.getControl('Add').click()
    return 'Calendar for' in browser.contents


def gradebook_scores_view(browser, section):
    browser.open('http://localhost/sections/%s' % section)
    browser.getLink('Gradebook').click()
    return 'SchoolTool origin' in browser.contents

def gradebook_scores_edit(browser, section):
    gradebook_scores_view(browser, section)
    browser.getLink('SchoolTool origin').click()
    browser.getControl(name='student1').value = '2'
    browser.getControl('Update').click()
    return 'SchoolTool origin' in browser.contents


def section_attendance_view(browser, section):
    browser.open('http://localhost/sections/%s/attendance/2005-09-12/09:30-10:25' % section)
    return 'Section attendance' in browser.contents

def section_attendance_edit(browser, section):
    section_attendance_view(browser, section)
    browser.getControl('Submit').click()
    return 'Section attendance' in browser.contents


def person_attendance_view(browser, subject):
    browser.open('http://localhost/persons/%s/@@attendance.html' % subject)
    return 'Attendance of' in browser.contents

def person_attendance_edit(browser, subject):
    return False


def calendar_overlays_edit(browser, subject):
    browser.open('http://localhost/persons/%s/calendar' % subject)
    browser.getControl('Apply').click()
    browser.getControl('More...').click()
    browser.getControl('SchoolTool  site-wide calendar').click()
    browser.getControl('Apply').click()
    return 'Calendar for' in browser.contents


def person_preferences_view(browser, subject):
    browser.open('http://localhost/persons/%s/preferences' % subject)
    return 'Calendar Preferences' in browser.contents

def person_preferences_edit(browser, subject):
    person_preferences_view(browser, subject)
    browser.getControl('Show periods').click()
    browser.getControl('Apply').click()
    browser.getControl('Show periods').click()
    browser.getControl('Apply').click()
    return 'Calendar Preferences' in browser.contents


def group_container_view(browser):
    go_home(browser)
    browser.getLink('Groups').click()
    return 'Teachers' in browser.contents

def group_container_edit(browser):
    group_container_view(browser)
    browser.getLink('New Group').click()
    browser.getControl('Title').value = 'Test Group'
    browser.getControl('Identifier').value = 'testgroup'
    browser.getControl('Add').click()
    browser.getControl(name='delete.testgroup').value = True
    browser.getControl('Delete').click()
    browser.getControl('Confirm').click()
    return 'Teachers' in browser.contents


def group_data_view(browser):
    go_home(browser)
    browser.open('http://localhost/groups/teachers')
    return 'Teacher1' in browser.contents

def group_data_edit(browser):
    group_data_view(browser)
    browser.getLink('edit members').click()
    browser.getControl('Frog').click()
    browser.getControl('Add').click()
    browser.getControl('Frog').click()
    browser.getControl('Remove').click()
    return True


def group_calendar_view(browser):
    browser.open('http://localhost/groups/teachers/calendar')
    return 'Calendar for' in browser.contents

def group_calendar_edit(browser):
    group_calendar_view(browser)
    browser.getLink('9:00').click()
    browser.getControl('Title').value = 'Test event'
    browser.getControl('Add').click()
    return 'Calendar for' in browser.contents


def resource_container_view(browser):
    go_home(browser)
    browser.getLink('Resources').click()
    return 'Time travel machine' in browser.contents

def resource_container_edit(browser):
    resource_container_view(browser)
    browser.getLink('New Resource').click()
    browser.getControl('Title').value = 'Test Resource'
    browser.getControl('Identifier').value = 'testresource'
    browser.getControl('Add').click()
    browser.getControl(name='delete.testresource').value = True
    browser.getControl('Delete').click()
    browser.getControl('Confirm').click()
    return 'Time travel machine' in browser.contents


def resource_data_view(browser):
    go_home(browser)
    browser.getLink('Resources').click()
    browser.getLink('Time travel machine').click()
    return 'Time travel machine' in browser.contents

def resource_data_edit(browser):
    resource_data_view(browser)
    browser.getLink('Edit Info').click()
    ctrl = browser.getControl('Description')
    ctrl.value = ctrl.value + 'broken. '
    browser.getControl('Apply').click()
    return True


def resource_calendar_view(browser):
    browser.open('http://localhost/resources/ttm/calendar')
    return 'Calendar for' in browser.contents

def resource_calendar_edit(browser):
    resource_calendar_view(browser)
    browser.getLink('9:00').click()
    browser.getControl('Title').value = 'Test event'
    browser.getControl('Add').click()
    return 'Calendar for' in browser.contents


def section_view(browser):
    browser.open('http://localhost/sections/history6a')
    return 'Section of' in browser.contents

def section_edit(browser):
    section_view(browser)
    browser.getLink('edit individuals').click()
    browser.getControl('Student3').click()
    browser.getControl('Add').click()
    browser.getControl('Student3').click()
    browser.getControl('Remove').click()
    return True


def section_activities_view(browser):
    section_view(browser)
    browser.getLink('Activities').click()
    return 'Activities' in browser.contents

def section_activities_edit(browser):
    section_activities_view(browser)
    browser.getLink('New Activity').click()
    browser.getControl('Title').value = 'Natural History'
    browser.getControl('Identifier').value = 'nathist'
    browser.getControl('Custom score system').click()
    browser.getControl('Add').click()
    browser.getControl(name='delete:list').value = ['nathist']
    browser.getControl('Delete').click()
    return 'Activities' in browser.contents


def section_calendar_view(browser):
    browser.open('http://localhost/sections/history6a/calendar')
    return 'Calendar for' in browser.contents

def section_calendar_edit(browser):
    section_calendar_view(browser)
    browser.getLink('9:00').click()
    browser.getControl('Title').value = 'Test event'
    browser.getControl('Add').click()
    return 'Calendar for' in browser.contents


def course_view(browser):
    go_home(browser)
    browser.getLink('Courses').click()
    browser.getLink('History 6').click()
    return 'History 6' in browser.contents

def course_edit(browser):
    course_view(browser)
    browser.getLink('New Section').click()
    browser.getControl('Code').value = 'edited-history'
    browser.getControl('Add').click()
    return 'History 6' in browser.contents


def course_activities_view(browser):
    browser.open('http://localhost/courses/history6/activities')
    return 'Activities' in browser.contents

def course_activities_edit(browser):
    course_activities_view(browser)
    browser.getLink('New Activity').click()
    browser.getControl('Title').value = 'Natural History'
    browser.getControl('Identifier').value = 'nathist'
    browser.getControl('Custom score system').click()
    browser.getControl('Add').click()
    browser.getControl(name='delete:list').value = ['nathist']
    browser.getControl('Delete').click()
    return 'Activities' in browser.contents


def schooltool_view(browser):
    go_home(browser)
    return 'SchoolTool' in browser.contents


def schooltool_info_view(browser):
    browser.open('http://localhost/persons/manager/@@site-preferences.html')
    return 'Change site preferences' in browser.contents

def schooltool_info_edit(browser):
    schooltool_info_view(browser)
    browser.getControl('Title').value = 'ToolSchool'
    browser.getControl('Apply').click()
    browser.getControl('Title').value = 'SchoolTool'
    browser.getControl('Apply').click()
    return True


def schooltool_calendar_view(browser):
    schooltool_view(browser)
    return 'Calendar for SchoolTool' in browser.contents

def schooltool_calendar_edit(browser):
    schooltool_calendar_view(browser)
    browser.getLink('9:00').click()
    browser.getControl('Title').value = 'Test event'
    browser.getControl('Add').click()
    return 'Calendar for' in browser.contents


def timetables_view(browser):
    go_home(browser)
    browser.getLink('School Timetables').click()
    return 'School Timetables' in browser.contents

def timetables_edit(browser):
    timetables_view(browser)
    browser.getLink('New Timetable').click()
    browser.getControl('Title').value = 'test timetable'
    browser.getControl('Next').click()
    browser.getControl('Days of the week').click()
    browser.getControl('Same time each day').click()
    browser.getControl('Next').click()
    browser.getControl('Designated by time').click()
    browser.getControl('No').click()
    return 'School Timetables' in browser.contents


def level_view(browser):
    go_home(browser)
    browser.getLink('Levels').click()
    return 'Level index' in browser.contents

def level_edit(browser):
    level_view(browser)
    browser.getLink('New Level').click()
    browser.getControl('Title').value = 'Bonus level'
    browser.getControl('Identifier').value = 'bonuslevel'
    browser.getControl('Add').click()
    browser.getControl(name='delete.bonuslevel').value = True
    browser.getControl('Delete').click()
    browser.getControl('Confirm').click()
    return 'Level index' in browser.contents


def permissions_view(browser):
    go_home(browser)
    browser.getLink('Access Control').click()
    return 'Access Control' in browser.contents

def permissions_edit(browser):
    permissions_view(browser)
    browser.getControl('Everyone can view the application calendar').click()
    browser.getControl('Apply').click()
    browser.getControl('Everyone can view the application calendar').click()
    browser.getControl('Apply').click()
    return 'Access Control' in browser.contents


def term_view(browser):
    go_home(browser)
    browser.getLink('Terms').click()
    return 'Terms' in browser.contents

def term_edit(browser):
    term_view(browser)
    browser.getLink('New Term').click()
    browser.getControl('Title').value = 'SchoolTool summer term'
    browser.getControl('Start date').value = '2006-06-01'
    browser.getControl('End date').value = '2006-09-01'
    browser.getControl('Next').click()
    browser.getControl('Add term').click()
    return 'SchoolTool summer term' in browser.contents


def do_test(func, *args):
    try:
        return bool(func(*args))
    except Exception, e:
        return False


def raw_column(browser, subject, section):
    result = {'person container': (
              do_test(person_container_view, browser, subject),
              do_test(person_container_edit, browser, subject)),
              'person data': (
              do_test(person_data_view, browser, subject),
              do_test(person_data_edit, browser, subject)),
              'person calendar': (
              do_test(person_calendar_view, browser, subject),
              do_test(person_calendar_edit, browser, subject)),
              'gradebook scores': (
              do_test(gradebook_scores_view, browser, section),
              do_test(gradebook_scores_edit, browser, section)),
              'section attendance': (
              do_test(section_attendance_view, browser, section),
              do_test(section_attendance_edit, browser, section)),
              'person attendance': (
              do_test(person_attendance_view, browser, subject),
              do_test(person_attendance_edit, browser, subject)),
              'overlay calendar': (
              None,
              do_test(calendar_overlays_edit, browser, subject)),
              'person preferences': (
              do_test(person_preferences_view, browser, subject),
              do_test(person_preferences_edit, browser, subject)),
              'group container': (
              do_test(group_container_view, browser),
              do_test(group_container_edit, browser)),
              'group data': (
              do_test(group_data_view, browser),
              do_test(group_data_edit, browser)),
              'group calendar': (
              do_test(group_calendar_view, browser),
              do_test(group_calendar_edit, browser)),
              'resource container': (
              do_test(resource_container_view, browser),
              do_test(resource_container_edit, browser)),
              'resource data': (
              do_test(resource_data_view, browser),
              do_test(resource_data_edit, browser)),
              'resource calendar': (
              do_test(resource_calendar_view, browser),
              do_test(resource_calendar_edit, browser)),
              'section': (
              do_test(section_view, browser),
              do_test(section_edit, browser)),
              'section activities': (
              do_test(section_activities_view, browser),
              do_test(section_activities_edit, browser)),
              'section calendar': (
              do_test(section_calendar_view, browser),
              do_test(section_calendar_edit, browser)),
              'course': (
              do_test(course_view, browser),
              do_test(course_edit, browser)),
              'course activities': (
              do_test(course_activities_view, browser),
              do_test(course_activities_edit, browser)),
              'schooltool': (
              do_test(schooltool_view, browser),
              None),
              'schooltool info': (
              do_test(schooltool_info_view, browser),
              do_test(schooltool_info_edit, browser)),
              'schooltool calendar': (
              do_test(schooltool_calendar_view, browser),
              do_test(schooltool_calendar_edit, browser)),
              'timetables': (
              do_test(timetables_view, browser),
              do_test(timetables_edit, browser)),
              'level': (
              do_test(level_view, browser),
              do_test(level_edit, browser)),
              'term': (
              do_test(term_view, browser),
              do_test(term_edit, browser)),
              'permissions': (
              do_test(permissions_view, browser),
              do_test(permissions_edit, browser)),
              }
    return result


def column(browser, *args):
    result = raw_column(browser, *args)
    for i in sorted(result.items()):
        out = '%s:' % i[0]
        if i[1][0]:
            out += ' view'
        if i[1][1]:
            out += ' edit'
        print out

def column2(browser, *args):
    result = raw_column(browser, *args)
    for i in sorted(result.items()):
        out = '%s:' % i[0]
        if i[1][0]:
            out += ' view'
        if i[1][1]:
            out += ' edit'
        print '%s: %s %s' % (i[0], i[1][0], i[1][1])