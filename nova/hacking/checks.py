# Copyright (c) 2012, Cloudscaling
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re

import pep8

"""
Guidelines for writing new hacking checks

 - Use only for Nova specific tests. OpenStack general tests
   should be submitted to the common 'hacking' module.
 - Pick numbers in the range N3xx. Find the current test with
   the highest allocated number and then pick the next value.
 - Keep the test method code in the source file ordered based
   on the N3xx value.
 - List the new rule in the top level HACKING.rst file
 - Add test cases for each new rule to nova/tests/test_hacking.py

"""

session_check = re.compile(r"\w*def [a-zA-Z0-9].*[(].*session.*[)]")
cfg_re = re.compile(r".*\scfg\.")
vi_header_re = re.compile(r"^#\s+vim?:.+")
virt_file_re = re.compile(r"\./nova/(?:tests/)?virt/(\w+)/")
virt_import_re = re.compile(
    r"^\s*(?:import|from) nova\.(?:tests\.)?virt\.(\w+)")
virt_config_re = re.compile(
    r"CONF\.import_opt\('.*?', 'nova\.virt\.(\w+)('|.)")
author_tag_re = (re.compile("^\s*#\s*@?(a|A)uthor:"),
                 re.compile("^\.\.\s+moduleauthor::"))
asse_trueinst_re = re.compile(
                     r"(.)*assertTrue\(isinstance\((\w|\.|\'|\"|\[|\])+, "
                     "(\w|\.|\'|\"|\[|\])+\)\)")
asse_equal_type_re = re.compile(
                       r"(.)*assertEqual\(type\((\w|\.|\'|\"|\[|\])+\), "
                       "(\w|\.|\'|\"|\[|\])+\)")
asse_equal_end_with_none_re = re.compile(
                           r"(.)*assertEqual\((\w|\.|\'|\"|\[|\])+, None\)")
asse_equal_start_with_none_re = re.compile(
                           r"(.)*assertEqual\(None, (\w|\.|\'|\"|\[|\])+\)")
conf_attribute_set_re = re.compile(r"CONF\.[a-z0-9_.]+\s*=\s*\w")
log_translation = re.compile(
    r"(.)*LOG\.(audit|error|info|warn|warning|critical|exception)\(\s*('|\")")
mutable_default_args = re.compile(r"^\s*def .+\((.+=\{\}|.+=\[\])")


def import_no_db_in_virt(logical_line, filename):
    """Check for db calls from nova/virt

    As of grizzly-2 all the database calls have been removed from
    nova/virt, and we want to keep it that way.

    N307
    """
    if "nova/virt" in filename and not filename.endswith("fake.py"):
        if logical_line.startswith("from nova import db"):
            yield (0, "N307: nova.db import not allowed in nova/virt/*")


def no_db_session_in_public_api(logical_line, filename):
    if "db/api.py" in filename or "db/sqlalchemy/api.py" in filename:
        if session_check.match(logical_line):
            yield (0, "N309: public db api methods may not accept session")


def use_timeutils_utcnow(logical_line):
    msg = "N310: timeutils.utcnow() must be used instead of datetime.%s()"

    datetime_funcs = ['now', 'utcnow']
    for f in datetime_funcs:
        pos = logical_line.find('datetime.%s' % f)
        if pos != -1:
            yield (pos, msg % f)


def _get_virt_name(regex, data):
    m = regex.match(data)
    if m is None:
        return None
    driver = m.group(1)
    # Ignore things we mis-detect as virt drivers in the regex
    if driver in ["test_virt_drivers", "driver", "firewall",
                  "disk", "api", "imagecache", "cpu", "hardware"]:
        return None
    # TODO(berrange): remove once bugs 1261826 and 126182 are
    # fixed, or baremetal driver is removed, which is first.
    if driver == "baremetal":
        return None
    return driver


def import_no_virt_driver_import_deps(physical_line, filename):
    """Check virt drivers' modules aren't imported by other drivers

    Modules under each virt driver's directory are
    considered private to that virt driver. Other drivers
    in Nova must not access those drivers. Any code that
    is to be shared should be refactored into a common
    module

    N311
    """
    thisdriver = _get_virt_name(virt_file_re, filename)
    thatdriver = _get_virt_name(virt_import_re, physical_line)
    if (thatdriver is not None and
        thisdriver is not None and
        thisdriver != thatdriver):
        return (0, "N311: importing code from other virt drivers forbidden")


def import_no_virt_driver_config_deps(physical_line, filename):
    """Check virt drivers' config vars aren't used by other drivers

    Modules under each virt driver's directory are
    considered private to that virt driver. Other drivers
    in Nova must not use their config vars. Any config vars
    that are to be shared should be moved into a common module

    N312
    """
    thisdriver = _get_virt_name(virt_file_re, filename)
    thatdriver = _get_virt_name(virt_config_re, physical_line)
    if (thatdriver is not None and
        thisdriver is not None and
        thisdriver != thatdriver):
        return (0, "N312: using config vars from other virt drivers forbidden")


def capital_cfg_help(logical_line, tokens):
    msg = "N313: capitalize help string"

    if cfg_re.match(logical_line):
        for t in range(len(tokens)):
            if tokens[t][1] == "help":
                txt = tokens[t + 2][1]
                if len(txt) > 1 and txt[1].islower():
                    yield(0, msg)


def no_vi_headers(physical_line, line_number, lines):
    """Check for vi editor configuration in source files.

    By default vi modelines can only appear in the first or
    last 5 lines of a source file.

    N314
    """
    # NOTE(gilliard): line_number is 1-indexed
    if line_number <= 5 or line_number > len(lines) - 5:
        if vi_header_re.match(physical_line):
            return 0, "N314: Don't put vi configuration in source files"


def no_author_tags(physical_line):
    for regex in author_tag_re:
        if regex.match(physical_line):
            physical_line = physical_line.lower()
            pos = physical_line.find('moduleauthor')
            if pos < 0:
                pos = physical_line.find('author')
            return pos, "N315: Don't use author tags"


def assert_true_instance(logical_line):
    """Check for assertTrue(isinstance(a, b)) sentences

    N316
    """
    if asse_trueinst_re.match(logical_line):
        yield (0, "N316: assertTrue(isinstance(a, b)) sentences not allowed")


def assert_equal_type(logical_line):
    """Check for assertEqual(type(A), B) sentences

    N317
    """
    if asse_equal_type_re.match(logical_line):
        yield (0, "N317: assertEqual(type(A), B) sentences not allowed")


def assert_equal_none(logical_line):
    """Check for assertEqual(A, None) or assertEqual(None, A) sentences

    N318
    """
    res = (asse_equal_start_with_none_re.match(logical_line) or
           asse_equal_end_with_none_re.match(logical_line))
    if res:
        yield (0, "N318: assertEqual(A, None) or assertEqual(None, A) "
               "sentences not allowed")


def no_translate_debug_logs(logical_line, filename):
    """Check for 'LOG.debug(_('

    As per our translation policy,
    https://wiki.openstack.org/wiki/LoggingStandards#Log_Translation
    we shouldn't translate debug level logs.

    * This check assumes that 'LOG' is a logger.
    * Use filename so we can start enforcing this in specific folders instead
      of needing to do so all at once.

    N319
    """
    if logical_line.startswith("LOG.debug(_("):
        yield(0, "N319 Don't translate debug level logs")


def no_setting_conf_directly_in_tests(logical_line, filename):
    """Check for setting CONF.* attributes directly in tests

    The value can leak out of tests affecting how subsequent tests run.
    Using self.flags(option=value) is the preferred method to temporarily
    set config options in tests.

    N320
    """
    if 'nova/tests/' in filename:
        res = conf_attribute_set_re.match(logical_line)
        if res:
            yield (0, "N320: Setting CONF.* attributes directly in tests is "
                      "forbidden. Use self.flags(option=value) instead")


def validate_log_translations(logical_line, physical_line, filename):
    # Translations are not required in the test directory
    # and the Xen utilities
    if ("nova/tests" in filename or
            "plugins/xenserver/xenapi/etc/xapi.d" in filename):
        return
    if pep8.noqa(physical_line):
        return
    msg = "N321: Log messages require translations!"
    if log_translation.match(logical_line):
        yield (0, msg)


def no_mutable_default_args(logical_line):
    msg = "N322: Method's default argument shouldn't be mutable!"
    if mutable_default_args.match(logical_line):
        yield (0, msg)


def factory(register):
    register(import_no_db_in_virt)
    register(no_db_session_in_public_api)
    register(use_timeutils_utcnow)
    register(import_no_virt_driver_import_deps)
    register(import_no_virt_driver_config_deps)
    register(capital_cfg_help)
    register(no_vi_headers)
    register(no_author_tags)
    register(assert_true_instance)
    register(assert_equal_type)
    register(assert_equal_none)
    register(no_translate_debug_logs)
    register(no_setting_conf_directly_in_tests)
    register(validate_log_translations)
    register(no_mutable_default_args)
