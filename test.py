#!/usr/bin/env python2.3
#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2003 Shuttleworth Foundation
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
SchoolTool test runner.

Syntax: test.py [options] [pathname-regexp [test-regexp]]

Test cases are located in the directory tree starting at the location of this
script, in subdirectories named 'tests', files named 'test*.py'.  They are then
filtered according to pathname and test regexes.

A leading "!" in a regexp is stripped and negates the regexp.  Pathname
regexp is applied to the whole path (package/package/module.py). Test regexp
is applied to a full test id (package.package.module.class.test_method).

Options:
  -h            print this help message
  -v            verbose (print dots for each test run)
  -vv           very verbose (print test names)
  -p            show progress bar (can be combined with -v or -vv)
  --list-files  list all files that match pathname-regexp
  --list-tests  list all tests that match test-regexp
"""
#
# This script borrows ideas from Zope 3's test runner heavily.  It is smaller
# and cleaner though, at the expense of more limited functionality.
#

import re
import os
import sys
import getopt
import unittest
import traceback

__metaclass__ = type


class Options:
    """Configurable properties of the test runner."""

    verbosity = 0
    progress = False
    pathname_regex = ''
    test_regex = ''
    list_files = False
    list_tests = False
    run_tests = True

    # these are hardcoded for the moment
    basedir = ''
    follow_symlinks = True
    immediate_errors = True
    screen_width = 80


def compile_matcher(regex):
    """Returns a function that takes one argument and returns True or False.

    Regex is a regular expression.  Empty regex matches everything.  There
    is one expression: if the regex starts with "!", the meaning of it is
    reversed.
    """
    if not regex:
        return lambda x: True
    elif regex == '!':
        return lambda x: False
    elif regex.startswith('!'):
        rx = re.compile(regex[1:])
        return lambda x: rx.search(x) is None
    else:
        rx = re.compile(regex)
        return lambda x: rx.search(x) is not None


def walk_with_symlinks(top, func, arg):
    """Like os.path.walk, but follows symlinks on POSIX systems.

    If the symlinks create a loop, this function will never finish.
    """
    try:
        names = os.listdir(top)
    except os.error:
        return
    func(arg, top, names)
    exceptions = ('.', '..')
    for name in names:
        if name not in exceptions:
            name = os.path.join(top, name)
            if os.path.isdir(name):
                walk_with_symlinks(name, func, arg)


def get_test_files(cfg):
    """Returns a list of test module filenames."""
    matcher = compile_matcher(cfg.pathname_regex)
    results = []
    def visit(ignored, dir, files):
        if os.path.basename(dir) != 'tests':
            return
        if '__init__.py' not in files:
            print >> sys.stderr, "%s is not a package" % dir
            return
        for file in files:
            if file.startswith('test') and file.endswith('.py'):
                path = os.path.join(dir, file)
                if matcher(path):
                    results.append(path)
    if cfg.follow_symlinks:
        walker = walk_with_symlinks
    else:
        walker = os.path.walk
    walker(cfg.basedir, visit, None)
    return results


def import_module(filename, cfg):
    """Imports and returns a module."""
    filename = os.path.splitext(filename)[0]
    modname = filename[len(cfg.basedir):].replace(os.path.sep, '.')
    if modname.startswith('.'):
        modname = modname[1:]
    mod = __import__(modname)
    components = modname.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def filter_testsuite(suite, matcher):
    """Returns a flattened list of test cases that match the given matcher."""
    if not isinstance(suite, unittest.TestSuite):
        raise TypeError('not a TestSuite', suite)
    results = []
    for test in suite._tests:
        if isinstance(test, unittest.TestCase):
            testname = test.id() # package.module.class.method
            if matcher(testname):
                results.append(test)
        else:
            filtered = filter_testsuite(test, matcher)
            results.extend(filtered)
    return results


def get_test_cases(test_files, cfg):
    """Returns a list of test cases from a given list of test modules."""
    matcher = compile_matcher(cfg.test_regex)
    results = []
    for file in test_files:
        module = import_module(file, cfg)
        test_suite = module.test_suite()
        filtered = filter_testsuite(test_suite, matcher)
        results.extend(filtered)
    return results


class CustomTestResult(unittest._TextTestResult):
    """Customised TestResult.

    It can show a progress bar, and displays tracebacks for errors and failures
    as soon as they happen, in addition to listing them all at the end.
    """

    __super = unittest._TextTestResult
    __super_init = __super.__init__
    __super_startTest = __super.startTest
    __super_printErrors = __super.printErrors

    def __init__(self, stream, descriptions, verbosity, count, cfg):
        self.__super_init(stream, descriptions, verbosity)
        self.count = count
        self.cfg = cfg
        if cfg.progress:
            self.dots = False
            self._lastWidth = 0
            self._maxWidth = cfg.screen_width - len("xxxx/xxxx (xxx.x%): ") - 1

    def startTest(self, test):
        if self.cfg.progress:
            # verbosity == 0: 'xxxx/xxxx (xxx.x%)'
            # verbosity == 1: 'xxxx/xxxx (xxx.x%): test name'
            # verbosity >= 2: 'xxxx/xxxx (xxx.x%): test name ... ok'
            n = self.testsRun + 1
            self.stream.write("\r%4d" % n)
            if self.count:
                self.stream.write("/%d (%5.1f%%)"
                                  % (self.count, n * 100.0 / self.count))
            if self.showAll: # self.cfg.verbosity == 1
                self.stream.write(": ")
            elif self.cfg.verbosity:
                name = self.getShortDescription(test)
                width = len(name)
                if width < self._lastWidth:
                    name += " " * (self._lastWidth - width)
                self.stream.write(": %s" % name)
                self._lastWidth = width
            self.stream.flush()
        self.__super_startTest(test)

    def getShortDescription(self, test):
        s = self.getDescription(test)
        if len(s) > self._maxWidth:
            # s is 'testname (package.module.class)'
            # try to shorten it to 'testname (...age.module.class)'
            # if it is still too long, shorten it to 'testnam...'
            # limit case is 'testname (...)'
            pos = s.find(" (")
            if pos + len(" (...)") > self._maxWidth:
                s = s[:self._maxWidth - 3] + "..."
            else:
                s = "%s...%s" % (s[:pos + 2], s[pos + 5 - self._maxWidth:])
        return s

    def printErrors(self):
        if self.cfg.progress and not (self.dots or self.showAll):
            self.stream.writeln()
        self.__super_printErrors()

    def formatError(self, err):
        return "".join(traceback.format_exception(*err))

    def printTraceback(self, kind, test, err):
        self.stream.writeln()
        self.stream.writeln()
        self.stream.writeln("%s: %s" % (kind, test))
        self.stream.writeln(self.formatError(err))
        self.stream.writeln()

    def addFailure(self, test, err):
        if self.cfg.immediate_errors:
            self.printTraceback("FAIL", test, err)
        self.failures.append((test, self.formatError(err)))

    def addError(self, test, err):
        if self.cfg.immediate_errors:
            self.printTraceback("ERROR", test, err)
        self.errors.append((test, self.formatError(err)))


class CustomTestRunner(unittest.TextTestRunner):
    """Customised TestRunner.

    See CustomisedTextResult for a list of extensions.
    """

    __super = unittest.TextTestRunner
    __super_init = __super.__init__
    __super_run = __super.run

    def __init__(self, cfg):
        self.__super_init(verbosity=cfg.verbosity)
        self.cfg = cfg

    def run(self, test):
        self.count = test.countTestCases()
        return self.__super_run(test)

    def _makeResult(self):
        return CustomTestResult(self.stream, self.descriptions, self.verbosity,
                                cfg=self.cfg, count=self.count)


def main(argv):
    """Main program."""

    # Defaults
    cfg = Options()
    cfg.basedir = os.path.dirname(argv[0])
    if not cfg.basedir:
        cfg.basedir = '.'

    # Option processing
    opts, args = getopt.getopt(argv[1:], 'hvp', ['list-files', 'list-tests'])
    for k, v in opts:
        if k == '-h':
            print __doc__
            return 0
        elif k == '-v':
            cfg.verbosity += 1
        elif k == '-p':
            cfg.progress = True
        elif k == '--list-files':
            cfg.list_files = True
            cfg.run_tests = False
        elif k == '--list-tests':
            cfg.list_tests = True
            cfg.run_tests = False
        else:
            print >> sys.stderr, '%s: invalid option: %s' % (argv[0], k)
            print >> sys.stderr, 'run %s -h for help'
            return 1
    if args:
        cfg.pathname_regex = args[0]
    if len(args) > 1:
        cfg.test_regex = args[1]
    if len(args) > 2:
        print >> sys.stderr, '%s: too many arguments: %s' % (argv[0], args[2])
        print >> sys.stderr, 'run %s -h for help'
        return 1

    # Environment
    if sys.version_info < (2, 3):
        print >> sys.stderr, '%s: need Python 2.3 or later' % argv[0]
        print >> sys.stderr, 'your python is %s' % sys.version
        return 1

    # Finding and importing
    test_files = get_test_files(cfg)
    test_cases = get_test_cases(test_files, cfg)

    # Configure the logging module
    import logging
    logging.basicConfig()
    logging.root.setLevel(logging.CRITICAL)

    # Running
    if cfg.list_files:
        print "\n".join(test_files)
    if cfg.list_tests:
        print "\n".join([test.id() for test in test_cases])
    if cfg.run_tests:
        runner = CustomTestRunner(cfg)
        suite = unittest.TestSuite()
        suite.addTests(test_cases)
        runner.run(suite)

    # That's all
    return 0


if __name__ == '__main__':
    exitcode = main(sys.argv)
    sys.exit(exitcode)
