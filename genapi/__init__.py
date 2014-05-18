import re
import urlparse

import requests
import slumber


class GenAuth(requests.auth.AuthBase):

    """Attach HTTP Genesis Authentication to Request object."""

    def __init__(self, username, password, url):
        payload = {
            'username': username,
            'password': password
        }

        r = requests.post(url + '/user/ajax/login/', data=payload)
        if not ('sessionid' in r.cookies and 'csrftoken' in r.cookies):
            raise Exception('Invalid credentials or url.')

        self.sessionid = r.cookies['sessionid']
        self.csrftoken = r.cookies['csrftoken']

    def __call__(self, r):
        # modify and return the request
        r.headers['Cookie'] = 'csrftoken={}; sessionid={}'.format(self.csrftoken, self.sessionid)
        return r



class GenObject(object):

    """Genesis data object annotation."""

    def __init__(self, data):
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
            self.annotation[f] = data[f]

        self.name = data['static']['name'] if 'name' in data['static'] else ''

        self.annotation.update(self._flatten_field(data['input'], data['input_schema'], 'input'))
        self.annotation.update(self._flatten_field(data['output'], data['output_schema'], 'output'))
        self.annotation.update(self._flatten_field(data['static'], data['static_schema'], 'static'))
        self.annotation.update(self._flatten_field(data['var'], data['var_template'], 'var'))

    def _flatten_field(self, field, schema, path):
        a = {}
        for field_schema, fields, path in iterate_schema(field, schema, path):
            name = field_schema['name']
            typ = field_schema['type']
            value = fields[name] if name in fields else None
            a[path] = {'name': name, 'value': value, 'type': typ}

        return a

    def __str__(self):
        return unicode(self.name).encode('utf-8')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"GenObject: {} - {}".format(self.id, self.name)


class GenProject(object):

    """Genesais project annotation."""

    def __init__(self, data, gencloud):
        for field in data:
            setattr(self, field, data[field])

        self.gencloud = gencloud

    def data_types(self):
        """Return a list of data types."""
        data = self.gencloud.project_objects(self.id)
        return sorted(set(d.type for d in data))

    def objects(self, **query):
        """Query for Data object annotation."""
        data = self.gencloud.project_objects(self.id)
        query['case_ids__contains'] = self.id
        ids = set(d['id'] for d in self.gencloud.api.dataid.get(**query)['objects'])
        return [d for d in data if d.id in ids]

    def find(self, filter):
        """Filter Data object annotation."""
        raise NotImplementedError()

    def __str__(self):
        return unicode(self.name).encode('utf-8')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"GenProject: {} - {}".format(self.id, self.name)


class GenCloud(object):

    """Python API for the Genesis platform."""

    def __init__(self, username, password, url='http://cloud.genialis.com'):
        self.api = slumber.API(urlparse.urljoin(url, 'api/v1/'),
            auth=GenAuth(username, password, url))

        self.cache = {'objects': {}, 'projects': None, 'project_objects': {}}

    def projects(self):
        """Return a list :obj:`GenProject` projects."""
        if not ('projects' in self.cache and self.cache['projects']):
            self.cache['projects'] = {c['id']: GenProject(c, self) for c in self.api.case.get()['objects']}

        return self.cache['projects']

    def project_objects(self, project_id):
        """Return a list of Data objects for given project.

        :param project_id: UUID of Genesis project
        :type project_id: string

        """
        projobjects = self.cache['project_objects']
        objects = self.cache['objects']

        if not project_id in projobjects:
            projobjects[project_id] = []
            data = self.api.data.get(case_ids__contains=project_id)['objects']
            for d in data:
                uuid = d['id']
                if uuid in objects:
                    # Update existing object
                    objects[uuid].update(d)
                else:
                    # Insert new object
                    objects[uuid] = GenObject(d)

                projobjects[project_id].append(objects[uuid])

            # hydrate reference fields
            for d in projobjects[project_id][27:]:
                #self._hydrate_refs(d['input'], d['input_schema'])
                break

        return projobjects[project_id]

    def download_data(self, objects, field):
        """Download files of data objects.

        :rtype: list of file handles

        """
        raise NotImplementedError()


    def _hydrate_refs(self, input, input_schema):
        """Hydrate references with linked data.

        Find fields with complex data:<...>: types.
        Assign a data reference that corresponds to those fields.

        """
        for field_schema, fields in iterate_fields(input, input_schema):
            name = field_schema['name']
            value = fields[name]
            if 'type' in field_schema:
                if field_schema['type'].startswith('data:'):
                    if re.match('^[0-9a-fA-F]{24}$', str(value)) is None:
                        print "ERROR: data:<...> value in field \"{}\", type \"{}\" not ObjectId but {}.".format(
                            name, field_schema['type'], value)

                    fields[name] = self.cache['objects'][value]

                elif field_schema['type'].startswith('list:data:'):
                    outputs = []
                    for val in value:
                        if re.match('^[0-9a-fA-F]{24}$', str(val)) is None:
                            print "ERROR: data:<...> value in {}, type \"{}\" not ObjectId but {}.".format(
                                name, field_schema['type'], val)

                        outputs.append(self.cache['objects'][val])

                    fields[name] = outputs


def iterate_fields(fields, schema):
    """Recursively iterate over all DictField sub-fields."""
    schema_dict = {val['name']: val for val in schema}
    for field_id, properties in fields.iteritems():
        if 'group' in schema_dict[field_id]:
            for _field_schema, _fields in iterate_fields(properties, schema_dict[field_id]['group']):
                yield (_field_schema, _fields)
        else:
            yield (schema_dict[field_id], fields)


def iterate_schema(fields, schema, path=None):
    """Recursively iterate over all schema sub-fields."""
    for field_schema in schema:
        name = field_schema['name']
        if 'group' in field_schema:
            for rvals in iterate_schema(fields[name] if name in fields else {},
                                        field_schema['group'],
                                        None if path is None else '{}.{}'.format(path, name)):
                yield rvals
        else:
            if path is None:
                yield (field_schema, fields)
            else:
                yield (field_schema, fields, '{}.{}'.format(path, name))


if __name__ == '__main__':
    g = GenCloud('admin', 'admin', 'http://gendev:10180')
    p = g.projects().itervalues().next()
    o = p.objects()
