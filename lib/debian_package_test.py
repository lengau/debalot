#!/usr/bin/python
# -*- coding:utf-8 -*-

"""Tests for debian_package module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import mock
import os
import tempfile
import unittest

from debalot.lib.test_files import test_data
from debalot.lib import debian_package
from debalot.lib import debian_package_pb2


class TestGenericProperties(unittest.TestCase):
    def setUp(self):
        self.object = mock.Mock()
        self.getter = debian_package._GenericProperty._property_getter(
            'property')

    def test_getter_no_field(self):
        self.object._pb.HasField.return_value = False
        self.assertIsNone(self.getter(self.object))

    def test_getter_with_field(self):
        self.object._pb.HasField.return_value = True
        self.assertIs(self.object._pb.property, self.getter(self.object))

    def test_setter(self):
        setter = debian_package._GenericProperty._property_setter('property')
        desired_value = mock.Mock()
        setter(self.object, desired_value)
        self.assertIs(self.object._pb.property, desired_value)

    def test_deleter(self):
        deleter = debian_package._GenericProperty._property_deleter('property')
        deleter(self.object)
        self.object._pb.ClearField.assert_called_once_with('property')


class TestGetUrgencyFromString(unittest.TestCase):
    def setUp(self):
        self.valid_urgency_strings = [
            'low',
            'medium',
            'high (EMERGENCY if you dun goofed)',
            'emergency ()',
            'critical (LOW (not likely) if nothing.)']
        self.valid_urgency_string_outputs = [
            (debian_package_pb2.LOW, None),
            (debian_package_pb2.MEDIUM, None),
            (debian_package_pb2.HIGH, 'EMERGENCY if you dun goofed'),
            (debian_package_pb2.EMERGENCY, ''),
            (debian_package_pb2.CRITICAL, 'LOW (not likely) if nothing.')]
        self.invalid_urgency_strings = [
            'not a valid urgency state',
            'invalid_state (VALID if something)']

    def test_valid_strings(self):
        output_urgency_states = []
        for string in self.valid_urgency_strings:
            output_urgency_states.append(
                debian_package.Changelog.get_urgency_from_string(string))
        self.assertItemsEqual(output_urgency_states,
                              self.valid_urgency_string_outputs)

    def test_invalid_strings(self):
        for string in self.invalid_urgency_strings:
            self.assertRaises(debian_package.UrgencyError,
                              debian_package.Changelog.get_urgency_from_string,
                              string)


class TestGetRelationshipString(unittest.TestCase):
    def setUp(self):
        # Called before the first testfunction is executed
        self.protobuf = debian_package_pb2.Relation()

    def test_invalid_type(self):
        self.assertRaises(
            TypeError,
            debian_package.Relation.get_relationship_string,
            'invalid type')

    def test_invalid_value(self):
        self.assertRaises(
            ValueError,
            debian_package.Relation.get_relationship_string,
            (-1))

    def test_enum_value(self):
        self.assertEqual(
            '=',
            debian_package.Relation.get_relationship_string(
                debian_package_pb2.Relation.EQUAL))

    def test_protobuf_has_relationship(self):
        self.protobuf.relationship = debian_package_pb2.Relation.EQUAL
        self.assertEqual(
            '=',
            debian_package.Relation.get_relationship_string(self.protobuf))

    def test_protobuf_no_relationship(self):
        self.protobuf.ClearField('relationship')
        self.assertIsNone(
            debian_package.Relation.get_relationship_string(self.protobuf))


class TestParseRelationship(unittest.TestCase):
    def test_invalid_type(self):
        self.assertRaises(
            TypeError,
            debian_package.Relation.parse_relationship,
            None)

    def test_invalid_enum_value(self):
        self.assertRaises(
            ValueError,
            debian_package.Relation.parse_relationship,
            -1)

    def test_valid_enum_value(self):
        for value in debian_package_pb2.Relation.Relationship.values():
            self.assertEqual(
                value,
                debian_package.Relation.parse_relationship(value))

    def test_invalid_string(self):
        self.assertRaises(
            ValueError,
            debian_package.Relation.parse_relationship,
            'invalid value')

    def test_valid_string(self):
        self.assertEqual(
            0,
            debian_package.Relation.parse_relationship('<'))


class TestInitialisePackages(unittest.TestCase):
    def test_package(self):
        self.assertRaises(AttributeError,
                          debian_package._Package)

    def test_sourcepackage_protobuf(self):
        source_protobuf = debian_package_pb2.SourcePackage()
        package = debian_package.SourcePackage(protobuf=source_protobuf)
        self.assertEqual(source_protobuf, package._pb)

    def test_sourcepackage_clean(self):
        package = debian_package.SourcePackage()
        self.assertIsInstance(package._pb, debian_package_pb2.SourcePackage)

    def test_sourcepackage_invalid(self):
        self.assertRaises(
            TypeError,
            debian_package.SourcePackage,
            protobuf='Not a protobuf')

    def test_binarypackage_protobuf(self):
        binary_protobuf = debian_package_pb2.BinaryPackage()
        package = debian_package.BinaryPackage(protobuf=binary_protobuf)
        self.assertEqual(binary_protobuf, package._pb)

    def test_binarypackage_clean(self):
        package = debian_package.BinaryPackage()
        self.assertIsInstance(package._pb, debian_package_pb2.BinaryPackage)

    def test_binarypackage_invalid(self):
        with self.assertRaises(TypeError):
            debian_package.BinaryPackage(protobuf='Not a protobuf')


class TestPackageClassFunctions(unittest.TestCase):
    def test_parse_priority_valid_strings(self):
        for key in debian_package_pb2.Priority.keys():
            self.assertIn(debian_package._Package.parse_priority(key),
                          debian_package_pb2.Priority.values())

    def test_parse_priority_invalid_strings(self):
        for key in ('invalid', 'this is totally a priority'):
            with self.assertRaisesRegexp(ValueError, 'Priority string .*'):
                debian_package._Package.parse_priority(key)

    def test_parse_priority_valid_integers(self):
        for value in debian_package_pb2.Priority.values():
            self.assertEqual(value,
                             debian_package._Package.parse_priority(value))

    def test_parse_priority_invalid_integers(self):
        for value in range(100, 1000):
            with self.assertRaisesRegexp(ValueError,
                                         'Unknown priority: %d' % value):
                debian_package._Package.parse_priority(value)

    def test_parse_priority_invalid_type(self):
        with self.assertRaises(TypeError):
            debian_package._Package.parse_priority({})


class TestSourcePackageControlImport(unittest.TestCase):
    def setUp(self):
        self.source_package = debian_package.SourcePackage()

    def test_parse_simple_string_fields(self):
        self.source_package._parse_control_line('Source: hello-debhelper\n')
        self.assertEqual('hello-debhelper', self.source_package._pb.name)
        self.source_package._parse_control_line('Section: oldlibs\n')
        self.assertEqual('oldlibs', self.source_package._pb.section)
        self.source_package._parse_control_line('Homepage: https://debian.org')
        self.assertEqual('https://debian.org',
                         self.source_package._pb.homepage)
        self.source_package._parse_control_line(
            'Vcs-Browser: https://example.org/\n')
        self.assertEqual('https://example.org/',
                         self.source_package._pb.vcs_browser)

    def test_parse_priority(self):
        self.source_package._parse_control_line('Priority: extra\n')
        self.assertEqual(4, self.source_package._pb.priority)
        for priority in debian_package_pb2.Priority.items():
            self.source_package._parse_control_line(
                'Priority: %s\n' % priority[0])
            self.assertEqual(priority[1], self.source_package._pb.priority)

    def test_parse_maintainer(self):
        self.source_package._parse_control_line(
            'Maintainer: Santiago Vila <sanvila@debian.org>\n')
        self.assertEqual('Santiago Vila', self.source_package.maintainer.name)
        self.assertEqual('sanvila@debian.org',
                         self.source_package.maintainer.email)

    def test_parse_uploaders(self):
        self.source_package._parse_control_line(
            'Uploaders: Alex Lowe <lengau@gmail.com>, '
            'Mark Shuttleworth <shuttleworth@ubuntu.com>\n')
        self.assertEqual('Alex Lowe', self.source_package.uploaders[0].name)
        self.assertEqual('lengau@gmail.com',
                         self.source_package.uploaders[0].email)
        self.assertEqual('Mark Shuttleworth',
                         self.source_package.uploaders[1].name)
        self.assertEqual('shuttleworth@ubuntu.com',
                         self.source_package.uploaders[1].email)

    def test_parse_standards_version(self):
        self.source_package._parse_control_line('Standards-Version: 3.9.5\n')
        # TODO: Figure out how to parse standards versions.

    def test_parse_build_depends_etc(self):
        self.source_package._parse_control_line(
            'Build-Depends: debhelper (>= 9)\n')
        # TODO: Parse Build Depends and the like.

    def test_parse_vcs_fields(self):
        self.source_package._parse_control_line(
            'Vcs-Git: https://github.com/lengau/debalot\n')
        # TODO: Parse VCS fields.

    def test_parse_generic_fields(self):
        generic_fields = {
            'Generic-Field': 'Generic value',
            'Other-Field': 'Other_value',
        }
        for field in generic_fields:
            self.source_package._parse_control_line(
                '%s: %s\n' % (field, generic_fields[field]))
        for field in self.source_package.additional_fields:
            self.assertIn(field.key, generic_fields)
            self.assertEqual(generic_fields[field.key], field.value)

    def test_import_control_file_valid_file(self):
        # TODO: Create this test.
        pass

    def test_import_control_file_invalid_file(self):
        # TODO: Create this test
        pass


class TestSourcePackageChangelog(unittest.TestCase):
    def setUp(self):
        self.changelog_source_filename = os.path.join(
            os.path.dirname(__file__), 'test_files/test_changelog')
        self.source_package = debian_package.SourcePackage()
        self.data_package = debian_package.SourcePackage(
            protobuf=test_data.SourcePackage.SOURCE_PACKAGE)
        self.addTypeEqualityFunc(debian_package_pb2.Change,
                                 self.assert_changes_equal)

    def assert_changes_equal(self, expected, actual, msg=None):
        self.assertEqual(expected.name, actual.name, msg=None)
        self.assertEqual(expected.version, actual.version, msg=None)
        self.assertEqual(expected.distributions, actual.distributions,
                         msg=None)
        self.assertEqual(expected.urgency, actual.urgency, msg=None)
        self.assertEqual(expected.entries, actual.entries, msg=None)
        self.assertEqual(expected.timestamp, actual.timestamp, msg=None)
        self.assertEqual(expected.timezone, actual.timezone, msg=None)
        self.assertEqual(expected.maintainer.name,
                         actual.maintainer.name, msg=None)
        self.assertEqual(expected.maintainer.email,
                         actual.maintainer.email, msg=None)

    def assert_changelogs_equal(self, expected, actual, msg=None):
        self.assertEqual(len(expected), len(actual), msg=None)
        for i in range(len(expected)):
            self.assertEqual(expected[i], actual[i], msg=None)

    def test_import_changelog_file_succeeds(self):
        with codecs.open(self.changelog_source_filename,
                         encoding='utf-8-sig') as changelog_source_file:
            self.source_package.import_changelog_file(changelog_source_file)
        expected = test_data.SourcePackage.SOURCE_PACKAGE.changelog
        actual = self.source_package._pb.changelog
        self.assert_changelogs_equal(expected, actual)

    def test_import_changelog_file_invalid_urgency(self):
        source_filename = self.changelog_source_filename + '_invalid_urgency'
        with codecs.open(source_filename,
                         encoding='utf-8') as changelog_source_file:
            with self.assertRaisesRegexp(debian_package.UrgencyError,
                                         'Invalid package urgency: .*'):
                self.source_package.import_changelog_file(
                    changelog_source_file)

    def test_import_changelog_file_invalid_keyword(self):
        source_filename = self.changelog_source_filename + '_invalid_keyword'
        with codecs.open(source_filename,
                         encoding='utf-8') as changelog_source_file:
            with self.assertRaisesRegexp(debian_package.KeywordError,
                                         ('Invalid changelog keyword: .*\. '
                                          'Valid keywords are: .*')):
                self.source_package.import_changelog_file(
                    changelog_source_file)

    def test_generate_changelog(self):
        output_changelog = [
            line for line in self.data_package.generate_changelog()]
        self.assertEqual(test_data.SourcePackage.OUTPUT_CHANGELOG,
                         output_changelog)

    def test_export_changelog_file(self):
        answer_filename = self.changelog_source_filename + '_fixed'
        with codecs.open(answer_filename, encoding='utf-8-sig') as f:
            expected = f.readlines()
        output_filename = tempfile.mkstemp(prefix='debalot_test_')[1]
        with codecs.open(output_filename, 'w+', encoding='utf-8') as output:
            self.data_package.export_changelog_file(output)
            output.seek(0)
            actual = output.readlines()
        self.assertEqual(expected, actual)
        os.remove(output_filename)


if __name__ == "__main__":
    unittest.main()
