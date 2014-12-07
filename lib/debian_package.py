""" Debian package classes.
Requires debian_pb2, generated from the debian_package protobuf.
"""

import calendar
from datetime import datetime
import dateutil.parser
import os
import string

import debian_package_pb2 as pb
import file


URGENCY_ERROR_VALUE = 'Invalid package urgency: %s'
KEYWORD_ERROR_VALUE = ('Invalid changelog keyword: "%s". '
                       'Valid keywords are: urgency')


class UrgencyError(ValueError):
    """Raised if a changelog urgency value is erroneous."""
    def __init__(self, urgency):
        self.urgency = urgency

    def __str__(self):
        return URGENCY_ERROR_VALUE % self.urgency


class KeywordError(ValueError):
    """Raised if a keyword value from a changelog is erroneous."""
    def __init__(self, keyword):
        self.keyword = keyword

    def __str__(self):
        return KEYWORD_ERROR_VALUE % self.keyword


class _GenericProperty(property):
    """A generic protobuf property.
    Most properties of classes in this module are simple wrappers around
    protobuf fields. Making a generic property and using closures makes
    these simple properties much more readable.

    Args:
        property_name: A string containing the name by which the property
            is known in debian_package.proto.
    Returns:
        A python property that should be named property_name
    """
    # TODO: Implement HasField for generic properties.
    def __new__(cls, property_name, docstring=None):
        return property(cls._property_getter(property_name),
                        cls._property_setter(property_name),
                        cls._property_deleter(property_name),
                        docstring)

    @classmethod
    def _property_getter(cls, property):
        def get(self):
            if not self._pb.HasField(property):
                return None
            return getattr(self._pb, property)
        return get

    @classmethod
    def _property_setter(cls, property):
        def set(self, value):
            setattr(self._pb, property, value)
        return set

    @classmethod
    def _property_deleter(cls, property):
        def delete(self):
            self._pb.ClearField(property)
        return delete


def get_urgency_from_string(string):
    """Get the urgency and its commentary from a string.

    From a keyword=value section of a changelog entry line, get the urgency
    enum value. If there is commentary, return it as well.

    Example strings:
    medium
    medium (HIGH for anyone who exposes this to the Internet)

    Args:
        string: The string containing the urgency and commentary.
    Returns:
        A tuple containing the urgency enum value and the commentary string.
        The commentary will be None (not a string) if there is no commentary.
    """
    split_field = string.strip().split(' (', 1)
    urgency = split_field[0].upper()
    if len(split_field) == 1:
        commentary = None
    else:
        commentary = split_field[1].strip(')')
    try:
        urgency_value = getattr(pb, urgency)
    except AttributeError:
        raise UrgencyError(urgency)
    return (urgency_value, commentary)


def get_time_string(timestamp, zone):
    """Get the time string for a changelong from a timestamp and time zone.

    Args:
        timestamp: integer timestamp value.
        zone: The timezone offset in minutes.
    returns:
        A time string for use in a debian/changelog file.
    """
    change_time = datetime.fromtimestamp(
        timestamp, tz=dateutil.tz.tzoffset(None, zone*60))
    return change_time.strftime('%a, %d %b %Y %H:%M:%S %z')


class Relation:
    """ A Debian package relation.

    This abstract class represents a related package for our package.
    For example, this could be a dependency, a conflict, or one of several
    other relationships.
    """
    _RELATIONSHIP_STRINGS = {
        # The first string in each tuple is the string that will be used as
        # the canonical form.
        u'STRICTLY_EARLIER': (
            u'<<', u'<',
            u'strictly earlier', u'strictly_earlier',
            u'less than', u'less_than', u'lt'),
        u'EARLIER_OR_EQUAL': (
            u'<=',
            u'less or equal', u'less_or_equal', u'leq',
            u'earlier or equal', u'earlier_or_equal',
            u'less than or equal to', u'less_than_or_equal_to'),
        u'EQUAL': (
            u'=', u'==', u'===',
            u'equal', u'eq', u'equal to', u'equals'),
        u'LATER_OR_EQUAL': (
            u'>=',
            u'greater or equal', u'greater_or_equal', u'geq',
            u'later or equal', u'later_or_equal',
            u'greater than or equal to', u'greater_than_or_equal_to'),
        u'STRICTLY_LATER': (
            u'>>', u'>',
            u'greater than', u'greater_than', u'gt',
            u'strictly later', u'strictly_later')}

    @classmethod
    def get_relationship_string(cls, relationship):
        """Get the canonical relationshp string from a Relation protobuf.

        Args:
            relationship: A relationship enum value or Relation protobuf.
        Returns:
            A string of the relationship to be used.
        """
        if isinstance(relationship, pb.Relation):
            if not relationship.HasField('relationship'):
                return None
            return cls.get_relationship_string(relationship.relationship)
        return cls._RELATIONSHIP_STRINGS[pb.Relation.Relationship.Name(
            relationship)][0]

    @classmethod
    def parse_relationship(cls, relationship):
        """Parse a relationship for setting a relationship field.

        Example use:
        x = debian_package_pb2.Relation()
        x.relationship = Relation.parse_relationship('>')

        Args:
            relationship: A string, integer, or enum of the relationship.
        Returns:
            A Relationship enum (as an integer).
        """
        UNDEFINED_RELATIONSHIP = (
            'Relationship must be one of the defined relationship values from '
            'the Debian Policy Manual. ')
        if isinstance(relationship, (str, unicode)):
            relationship = unicode(relationship.lower())
            for rel_type in cls._RELATIONSHIP_STRINGS:
                if relationship in cls._RELATIONSHIP_STRINGS[rel_type]:
                    return getattr(pb.Relation, rel_type)
            raise ValueError(UNDEFINED_RELATIONSHIP,
                             'See debian_package.py for all valid '
                             'relationship strings.')
        elif isinstance(relationship, int):
            if relationship in pb.Relation.Relationship.values():
                return relationship
            raise ValueError(
                UNDEFINED_RELATIONSHIP,
                'These correspond with the numbers 0-4 as integers. '
                'See debian_package.proto for more details.')
        else:
            raise TypeError(UNDEFINED_RELATIONSHIP,
                            'Only strings and integers (enum values) are '
                            'accepted for setting relationship values.')


class _Package(object):
    """ A generic Debian package.
    A _Package should never be instantiated or otherwise used except as a
    class parent for SourcePackage, BinaryPackage, and potential other package
    types.

    Attributes:
        name: A string containing the name of the package.
        TODO: _Package attributes
    """

    def __init__(self):
        if not hasattr(self, '_pb'):
            raise AttributeError(
                '__init__ function for %s did not initialise a protobuf before'
                ' calling _Package.__init__' % type(self))

        # These properties are passed through so external code can directly
        # modify the protobuf fields.
        # Some may later be replaced with our own properties.
        self.additional_field = self._pb.additional_field
        self.maintainer = self._pb.maintainer

    # These simple properties are given wrappers that allow a more pythonic
    # use, rather than using the Protocol Buffer API directly.
    name = _GenericProperty('name')
    section = _GenericProperty('section')
    priority = _GenericProperty('priority')
    homepage = _GenericProperty('homepage')


class SourcePackage(_Package):
    """A source package for Debian.

    A SourcePackage represents a Debian source package, as defined in the
    Debian Policy Manual, chapter 4.
    https://www.debian.org/doc/debian-policy/ch-source.html

    Attributes:
        TODO: SourcePackage attributes.
    """

    def __init__(self, protobuf=None):
        if isinstance(protobuf, pb.SourcePackage):
            self._pb = protobuf
        elif protobuf is None:
            self._pb = pb.SourcePackage()
        else:
            raise TypeError('Must import a SourcePackage protobuf. Imported:',
                            type(protobuf))
        _Package.__init__(self)

        # Many properties are easier to pass through straight to the protobuf
        # for now. Later we may define properties for them instead.
        self.uploader = self._pb.uploader

        self.build_depends = self._pb.build_depends
        self.build_depends_indep = self._pb.build_depends_indep
        self.build_conflicts = self._pb.build_conflicts
        self.build_conflicts_indep = self._pb.build_conflicts_indep

        self.standards_version = self._pb.standards_version
        self.changelog = self._pb.changelog

        self.binary_packages = self._pb.binary_packages

        self.vcs = self._pb.vcs

        self.original_tarball = self._pb.original_tarball

    vcs_browser = _GenericProperty('vcs_browser')

    def import_changelog_file(self, changelog):
        """Imports the changelog from a file. Extends current changelog.

        The changelog format looks like:
        package (version) distribution(s); urgency=urgency
            [optional blank line(s), stripped]
          * change details
            more change details
            [blank line(s), included in output of dpkg-parsechangelog]
          * even more change details
            [optional blank line(s), stripped]
         -- maintainer name <email address>[two spaces]  date

        where the 'p' in 'package' is in column 0.

        Args:
            changelog: A readable unicode file object containing the changelog.
        """
        changelog.seek(0)
        changes = []
        while True:
            change = pb.Change()
            changelog_line = file.next_nonempty_line(changelog)
            if changelog_line is None:
                break
            sections = changelog_line.split(';')
            words = sections[0].split()
            change.name = words[0]
            change.version = words[1].strip('()')
            # TODO: Check for multiple distributions
            change.distributions.extend(
                [word.strip(';') for word in words[2:]])
            # TODO: Better split the urgency.
            keyword_values = sections[1].split(',')
            for keyword_value in keyword_values:
                key_value = keyword_value.strip().split('=')
                if key_value[0] == 'urgency':
                    change.urgency, commentary = get_urgency_from_string(
                        key_value[1])
                    if commentary:
                        change.urgency_commentary = commentary
                else:
                    raise KeywordError(key_value[0])
            changelog_line = file.next_nonempty_line(changelog)
            entries = []
            while changelog_line[:3] != ' --':
                entries.append(changelog_line[2:-1])
                changelog_line = changelog.readline()
            while not entries[-1]:
                del entries[-1]
            change.entries.extend(entries)
            # TODO: Find an existing Person if it exists; otherwise create one.
            email_start = changelog_line.find('<')
            email_end = changelog_line.find('>')
            change.maintainer.name = changelog_line[4:email_start-1]
            change.maintainer.email = changelog_line[email_start+1:email_end]
            timestamp = dateutil.parser.parse(changelog_line[email_end+3:])
            change.timestamp = calendar.timegm(timestamp.utctimetuple())
            change.timezone = int(timestamp.tzinfo.utcoffset(
                timestamp.tzinfo).total_seconds()/60)
            changes.insert(0, change)
        self.changelog.extend(changes)

    def generate_changelog(self):
        """Generate a changelog for the package.

        Note that each entry will contain multiple lines, expressed as a list
        of strings.

        Yields:
            A changelog entry, from package name to timestamp.
        """
        for change in reversed(self.changelog):
            name = change.name or self.name
            urgency = pb.Urgency.Name(change.urgency).lower()
            if change.HasField('urgency_commentary'):
                urgency += ' ' + change.urgency_commentary
            yield (u'{name} ({version}) {distributions}; urgency={urgency}'
                   ).format(name=name, version=change.version,
                            distributions=' '.join(change.distributions),
                            urgency=urgency)
            yield u''
            for entry in change.entries:
                yield u'  %s' % entry if entry else u''
            yield u''
            yield (u' -- {maintainer.name} <{maintainer.email}>  {timestamp}'
                   ).format(maintainer=change.maintainer,
                            timestamp=get_time_string(change.timestamp,
                                                      change.timezone))
            yield u''

    def export_changelog_file(self, output_file):
        """Creates a changelog file from the changes in the source package.

        Args:
            output_file: A unicode output file object.
        """
        for line in self.generate_changelog():
            output_file.write(line + '\n')
        output_file.seek(-1, os.SEEK_END)
        output_file.truncate()


class BinaryPackage(_Package):
    """A binary package for Debian.

    A BinaryPackage represents a Debian binary package, as defined in the
    Debian Policy Manual, chapter 3.
    https://www.debian.org/doc/debian-policy/ch-binary.html

    Attributes:
        TODO: BinaryPackage attributes
    """
    def __init__(self, protobuf=None):
        if isinstance(protobuf, pb.BinaryPackage):
            self._pb = protobuf
        elif protobuf is None:
            self._pb = pb.BinaryPackage()
        else:
            raise TypeError('Must import a BinaryPackage protobuf. Imported:',
                            type(protobuf))

        _Package.__init__(self)

        # Properties where the user may directly modify the protobuf.
        # TODO: Replace relation pass-through properties with something better.
        self.depends = self._pb.depends
        self.recommends = self._pb.recommends
        self.suggests = self._pb.suggests
        self.enhances = self._pb.enhances
        self.pre_depends = self._pb.pre_depends
        self.conflicts = self._pb.conflicts
        self.breaks = self._pb.breaks
        self.replaces = self._pb.replaces

    architecture = _GenericProperty('architecture')
    version = _GenericProperty('version')
    essential = _GenericProperty('essential')
    provides = _GenericProperty('provides')
    description = _GenericProperty('description')
    package_type = _GenericProperty('package_type')
