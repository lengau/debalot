#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

""" Debian package classes.
Requires debian_package_pb2, generated from the debian_package protobuf.
"""
import debian_package_pb2 as pb


class Relation:
    """ A Debian package relation.

    This class represents a related package for our package. For example, this
    could be a dependency, a conflict, or one of several other relationships.

    Attributes:
        name: A string containing the name of the package upon which our
            parent package depends.
        version: A string containing the significant version number.
        relationship: The set of versions to which the parent package has a
            relationship.
        related_package: An object containing either the Package to which
            the parent package is related.
    """
    RELATIONSHIP_STRINGS = {
        'STRICTLY_EARLIER': '<<',
        'EARLIER_OR_EQUAL': '<=',
        'EQUAL': '=',
        'LATER_OR_EQUAL': '>=',
        'STRICTLY_LATER': '>>'
    }

    def __init__(self, name, version=None, relationship=None):
        self._relation_pb = pb.Relation()
        self.name = name
        if type(version) == str:
            self._relation_pb.version = version
            self.relationship = relationship

    @property
    def name(self):
        if not self._relation_pb.HasField('name'):
            return None
        return self._relation_pb.name

    @name.setter
    def name(self, name):
        self._relation_pb.name = name

    @name.deleter
    def name(self):
        self._relation_pb.ClearField('name')

    @property
    def relationship(self):
        if not self._relation_pb.HasField('relationship'):
            return None
        return self.RELATIONSHIP_STRINGS[pb.Relation.Relationship.Name(
            self._relation_pb.relationship)]

    @relationship.setter
    def relationship(self, relationship):
        UNDEFINED_RELATIONSHIP = (
            'Relationship must be one of the defined relationship values from '
            'the Debian Policy Manual. ')
        if relationship is None:
            del self.relationship
            return
        if type(relationship) in (str, unicode):
            rel_lower = relationship.lower()
            # NOTE: '<' for Earlier is deprecated, but still allowed.
            #       We will always use '<<'
            if rel_lower in {'<', '<<', 'strictly earlier', 'strictly_earlier',
                             'lt', 'less than', 'less_than'}:
                self._relation_pb.relationship = (
                    pb.Relation.STRICTLY_EARLIER)
            elif rel_lower in {'<=', 'less or equal', 'earlier or equal',
                               'less_or_equal', 'earlier_or_equal',
                               'less than or equal to',
                               'less_than_or_equal_to', 'leq'}:
                self._relation_pb.relationship = (
                    pb.Relation.EARLIER_OR_EQUAL)
            elif rel_lower in {'=', '==', '===', 'equal', 'eq'}:
                self._relation_pb.relationship = pb.Relation.EQUAL
            elif rel_lower in {'>=', 'greater or equal', 'later or equal',
                               'greater_or_equal', 'later_or_equal',
                               'greater than or equal to',
                               'greater_than_or_equal_to', 'geq'}:
                self._relation_pb.relationship = (
                    pb.Relation.LATER_OR_EQUAL)
            elif rel_lower in {'>', '>>', 'strictly later', 'gt',
                               'strictly_later', 'greater than',
                               'greater_than'}:
                self._relation_pb.relationship = (
                    pb.Relation.STRICTLY_LATER)
            else:
                raise ValueError(UNDEFINED_RELATIONSHIP,
                                 'See debian_package.py for a list of valid '
                                 'relationship strings.')
        elif type(relationship) == int:
            if 0 <= relationship <= 4:
                self._relation_pb.relationship = relationship
            else:
                raise ValueError(
                    UNDEFINED_RELATIONSHIP,
                    'These correspond with the numbers 0-4 as integers. '
                    'See debian_package.proto for more details.')
        else:
            raise ValueError(UNDEFINED_RELATIONSHIP,
                             'Only strings and integers (enum values) are '
                             'accepted for setting relationship values.')

    @relationship.deleter
    def relationship(self):
        self._relation_pb.ClearField('relationship')

    @property
    def version(self):
        if not self._relation_pb.HasField('version'):
            return None
        return self._relation_pb.version

    @version.setter
    def version(self, version):
        self._relation_pb.version = version

    @version.deleter
    def version(self):
        self._relation_pb.ClearField('version')
