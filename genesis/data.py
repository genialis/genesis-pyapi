"""Data"""
from __future__ import absolute_import, division, print_function, unicode_literals

from .utils import iterate_schema


class GenData(object):

    """Genesis data object annotation."""

    def __init__(self, data, gencloud):
        self.gencloud = gencloud
        self.update(data)

    def update(self, data):
        """Update the object with new data."""
        fields = [
            'id',
            'status',
            'type',
            'persistence',
            'date_start',
            'date_finish',
            'date_created',
            'date_modified',
            'checksum',
            'processor_name',
            'input',
            'input_schema',
            'output',
            'output_schema',
            'static',
            'static_schema',
            'var',
            'var_template',
        ]

        self.annotation = {}
        for f in fields:
            setattr(self, f, data[f])

        self.name = data['static']['name'] if 'name' in data['static'] else ''

        self.annotation.update(self._flatten_field(data['input'], data['input_schema'], 'input'))
        self.annotation.update(self._flatten_field(data['output'], data['output_schema'], 'output'))
        self.annotation.update(self._flatten_field(data['static'], data['static_schema'], 'static'))
        self.annotation.update(self._flatten_field(data['var'], data['var_template'], 'var'))

    def _flatten_field(self, field, schema, path):
        """Reduce dicts of dicts to dot separated keys."""
        flat = {}
        for field_schema, fields, path in iterate_schema(field, schema, path):
            name = field_schema['name']
            typ = field_schema['type']
            label = field_schema['label']
            value = fields[name] if name in fields else None
            flat[path] = {'name': name, 'value': value, 'type': typ, 'label': label}

        return flat

    def print_annotation(self):
        """Print annotation "key: value" pairs to standard output."""
        for path, ann in self.annotation.items():
            print("{}: {}".format(path, ann['value']))

    def print_downloads(self):
        """Print file fields to standard output."""
        for path, ann in self.annotation.items():
            if path.startswith('output') and ann['type'] == 'basic:file:':
                print("{}: {}".format(path, ann['value']['file']))

    def download(self, field):
        """Download a file.

        :param field: file field to download
        :type field: string
        :rtype: a file handle

        """
        if not field.startswith('output'):
            raise ValueError("Only processor results (output.* fields) can be downloaded")

        if field not in self.annotation:
            raise ValueError("Download field {} does not exist".format(field))

        ann = self.annotation[field]
        if ann['type'] != 'basic:file:':
            raise ValueError("Only basic:file: field can be downloaded")

        return next(self.gencloud.download([self.id], field))

    def __str__(self):
        return self.name

    def __repr__(self):
        return u"GenObject: {} - {}".format(self.id, self.name)
