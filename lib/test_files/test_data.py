﻿"""test_changelog in protobuf form."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import mock

from debalot.lib import debian_package_pb2


class SourcePackage():
    SOURCE_PACKAGE = debian_package_pb2.SourcePackage()
    SOURCE_PACKAGE.name = u'package'
    log = SOURCE_PACKAGE.changelog

    first_entry = log.add()
    second_entry = log.add()
    third_entry = log.add()
    fourth_entry = log.add()

    first_entry.name = u'some-package'
    first_entry.version = u'0.0.0'
    first_entry.distributions.append(u'stable')
    first_entry.urgency = debian_package_pb2.LOW
    first_entry.entries.append(u'* Initial release.')
    first_entry.timestamp = 10  # 10 seconds after epoch.
    first_entry.timezone = -300  # US Eastern Standard Time (UTC-5:00)
    first_entry.maintainer.name = u'Some Maintainer'
    first_entry.maintainer.email = u'maintainer@example.org'

    second_entry.name = u'package'
    second_entry.version = u'0.0.1-0ubuntu1~ubuntu70.04~ppa1'
    second_entry.distributions.extend([u'stable', u'testing'])
    second_entry.urgency = debian_package_pb2.MEDIUM
    second_entry.entries.append(u'* New upstream release. Also, trying out '
                                u'fancy version numbers and making this')
    second_entry.entries.append(u'  package available in testing. Multiline '
                                u'changelog entry.')
    second_entry.timestamp = 100
    second_entry.timezone = 0  # UTC
    second_entry.maintainer.name = u'Some Other Maintainer'
    second_entry.maintainer.email = u'other_guy@example.org'

    third_entry.name = u'package'
    third_entry.version = '0.0.2'
    third_entry.distributions.extend(
        [u'stable', u'testing', u'unstable', u'contrib'])
    third_entry.urgency = debian_package_pb2.LOW
    third_entry.urgency_commentary = (
        u'(HIGH if you were affected by some arbitrary bug or something)')
    third_entry.entries.append(
        u"* I don't like that optional blank line, so I'm not doing it.")
    third_entry.entries.append(u'* I do like multiple entries, though. '
                               u'Especially when one of the entries')
    third_entry.entries.append(u'  ends up going onto the next line.')
    third_entry.entries.append(
        u'* Even moreso if it\'s followed by another entry.')
    third_entry.entries.append(u'')
    third_entry.entries.append(
        u'* That space was intentional. Not putting one below here, though.')
    third_entry.timestamp = 1000
    third_entry.timezone = 120  # South Africa (UTC+2:00)
    third_entry.maintainer.name = u'Third maintainer person'
    third_entry.maintainer.email = u'someone@example.com'

    fourth_entry.name = u'package'
    fourth_entry.version = u'0.0.3'
    fourth_entry.distributions.append(u'stable')
    fourth_entry.urgency = debian_package_pb2.CRITICAL
    fourth_entry.entries.append(
        u'*A line here that doesn\'t have a space after the asterisk.')
    fourth_entry.entries.append(u'A line with no asterisk at all, not carrying'
                                u' on from a previous one.')
    fourth_entry.entries.append(u'[ One person ]')
    fourth_entry.entries.append(u'* I don\'t like empty lines at all')
    fourth_entry.entries.append(u'[ Other person ]')
    fourth_entry.entries.append(u'* This is really really super important. So '
                                u'important that I\'m going to write')
    fourth_entry.entries.append(
        u'  an entire paragraph telling you why, including:')
    fourth_entry.entries.append(u' - A random bullet point')
    fourth_entry.entries.append(u' - Actually make that two. Maybe more in '
                                u"just a bit. I'm not really sure. But")
    fourth_entry.entries.append(
        u'   first I want to interject with this second line')
    fourth_entry.entries.append(u" - Yeah, let's have a third bullet point.")
    fourth_entry.entries.append(u'* Oh, I like new lines so I\'m going to '
                                u'put in a few with some whitespace.')
    fourth_entry.entries.append(u'  They should be parsed out anyway. '
                                u'But the lack of a line before this and')
    fourth_entry.entries.append(u'  the next package entry is intentional.')
    fourth_entry.timestamp = 10000
    fourth_entry.timezone = 720  # New Zealand Standard Time (UTC+12:00)
    fourth_entry.maintainer.name = u'Someone brand new'
    fourth_entry.maintainer.email = u'brand_new@example.com'

    with codecs.open(u'lib/test_files/test_changelog_fixed',
                     encoding='utf-8-sig') as changelog:
        OUTPUT_CHANGELOG = changelog.read().splitlines()
    OUTPUT_CHANGELOG.append(u'')

VALID_SOURCE_PACKAGE = mock.Mock()
VALID_SOURCE_PACKAGE.name = 'hello-debhelper'
VALID_SOURCE_PACKAGE.section = 'oldlibs'
VALID_SOURCE_PACKAGE.priority = 4
VALID_SOURCE_PACKAGE.maintainer.name = 'Santiago Vila'
VALID_SOURCE_PACKAGE.maintainer.email = 'sanvila@debian.org'
VALID_SOURCE_PACKAGE.standards_version.major_version = 3
VALID_SOURCE_PACKAGE.standards_version.minor_version = 9
VALID_SOURCE_PACKAGE.standards_version.major_patch = 5
VALID_SOURCE_PACKAGE.standards_version.minor_patch = 1
DEPEND_DEBHELPER = mock.Mock()
DEPEND_DEBHELPER.name = 'debhelper'
DEPEND_DEBHELPER.version = '9'
DEPEND_DEBHELPER.relationship = 3  # Later or equal
VALID_SOURCE_PACKAGE.build_depends = [DEPEND_DEBHELPER]
