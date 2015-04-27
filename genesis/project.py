"""Project"""
from __future__ import absolute_import, division, print_function, unicode_literals


class GenProject(object):

    """Genesais project annotation."""

    def __init__(self, data, gencloud):
        for field in data:
            setattr(self, field, data[field])

        self.gencloud = gencloud
        self.id = getattr(self, 'id', None)  # pylint: disable=invalid-name
        self.name = getattr(self, 'name', None)

    def data_types(self):
        """Return a list of data types."""
        data = self.gencloud.project_data(self.id)
        return sorted(set(d.type for d in data))

    def data(self, **query):
        """Query for Data object annotation."""
        data = self.gencloud.project_data(self.id)
        query['case_ids__contains'] = self.id
        ids = set(d['id'] for d in self.gencloud.api.dataid.get(**query)['objects'])
        return [d for d in data if d.id in ids]

    def find(self, filter_str):
        """Filter Data object annotation."""
        raise NotImplementedError()

    def __str__(self):
        return self.name or 'n/a'

    def __repr__(self):
        return u"GenProject: {} - {}".format(self.id, self.name)
