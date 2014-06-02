import os
import re
import urlparse

import requests
import slumber


class GenAuth(requests.auth.AuthBase):

    """Attach HTTP Genesis Authentication to Request object."""

    def __init__(self, email, password, url):
        payload = {
            'email': email,
            'password': password
        }

        try:
            r = requests.post(url + '/user/ajax/login/', data=payload)
        except requests.exceptions.ConnectionError:
            raise Exception('Invalid url.')

        if r.status_code == 403:
            raise Exception('Invalid credentials.')

        if not ('sessionid' in r.cookies and 'csrftoken' in r.cookies):
            raise Exception('Invalid credentials.')

        self.sessionid = r.cookies['sessionid']
        self.csrftoken = r.cookies['csrftoken']

    def __call__(self, r):
        # modify and return the request
        r.headers['Cookie'] = 'csrftoken={}; sessionid={}'.format(self.csrftoken, self.sessionid)
        return r


class GenObject(object):

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
            #self.annotation[f] = data[f]

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

    def print_annotation(self):
        """Print annotation "key: value" pairs to standard output."""
        for path, a in self.annotation.iteritems():
            print "{}: {}".format(path, a['value'])

    def print_downloads(self):
        """Print file fields to standard output."""
        for path, a in self.annotation.iteritems():
            if path.startswith('output') and a['type'] == 'basic:file:':
                print "{}: {}".format(path, a['value']['file'])

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

        a = self.annotation[field]
        if a['type'] != 'basic:file:':
            raise ValueError("Only basic:file: field can be downloaded")

        return self.gencloud.download([self.id], field).next()

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

    def processors(self, **query):
        """Query for Processor objects."""
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

    def __init__(self, email='anonymous@genialis.com', password='anonymous', url='http://cloud.genialis.com'):
        self.url = url
        self.auth = GenAuth(email, password, url)
        self.api = slumber.API(urlparse.urljoin(url, 'api/v1/'), self.auth)

        self.cache = {'objects': {}, 'projects': None, 'project_objects': {}}

    def projects(self):
        """Return a list :obj:`GenProject` projects.

        :rtype: list of :obj:`GenProject` projects

        """
        if not ('projects' in self.cache and self.cache['projects']):
            self.cache['projects'] = {c['id']: GenProject(c, self) for c in self.api.case.get()['objects']}

        return self.cache['projects']

    def project_objects(self, project_id):
        """Return a list of Data objects for given project.

        :param project_id: UUID of Genesis project
        :type project_id: string
        :rtype: list of Data objects

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
                    objects[uuid] = GenObject(d, self)

                projobjects[project_id].append(objects[uuid])

            # Hydrate reference fields
            for d in projobjects[project_id]:
                while True:
                    ref_annotation = {}
                    remove_annotation = []
                    for path, a in d.annotation.iteritems():
                        if a['type'].startswith('data:'):
                            # Referenced data object found
                            # Copy annotation
                            ref_annotation.update({path + '.' + k: v for k, v in self.cache['objects'][a['value']].annotation.iteritems()})
                            remove_annotation.append(path)
                    if ref_annotation:
                        d.annotation.update(ref_annotation)
                        for path in remove_annotation:
                            del d.annotation[path]
                    else:
                        break


        return projobjects[project_id]

    def processors(self, project_id):
        """Return a list of Processor objects.

        :param project_id: UUID of Genesis project
        :type project_id: string
        :rtype: list of Processor objects

        """
        proc = self.api.processor.get()['objects']
        print proc
        return proc

    def download(self, objects, field):
        """Download files of data objects.

        :param objects: Data object ids
        :type objects: list of UUID strings
        :param field: Download field name
        :type field: string
        :rtype: generator of requests.Response objects

        """
        if not field.startswith('output'):
            raise ValueError("Only processor results (output.* fields) can be downloaded")

        for o in objects:
            o = str(o)
            if re.match('^[0-9a-fA-F]{24}$', o) is None:
                raise ValueError("Invalid object id {}".format(o))

            if field not in self.cache['objects'][o].annotation:
                raise ValueError("Download field {} does not exist".format(field))

            a = self.cache['objects'][o].annotation[field]
            if a['type'] != 'basic:file:':
                raise ValueError("Only basic:file: field can be downloaded")

        for o in objects:
            a = self.cache['objects'][o].annotation[field]
            url = urlparse.urljoin(self.url, 'api/v1/data/{}/download/{}'.format(o, a['value']['file']))
            yield requests.get(url, stream=True, auth=self.auth)


def iterate_fields(fields, schema):
    """Recursively iterate over all DictField sub-fields.

    :param fields: Field instance (e.g. input)
    :type fields: dict
    :param schema: Schema instance (e.g. input_schema)
    :type schema: dict

    """
    schema_dict = {val['name']: val for val in schema}
    for field_id, properties in fields.iteritems():
        if 'group' in schema_dict[field_id]:
            for _field_schema, _fields in iterate_fields(properties, schema_dict[field_id]['group']):
                yield (_field_schema, _fields)
        else:
            yield (schema_dict[field_id], fields)


def iterate_schema(fields, schema, path=None):
    """Recursively iterate over all schema sub-fields.

    :param fields: Field instance (e.g. input)
    :type fields: dict
    :param schema: Schema instance (e.g. input_schema)
    :type schema: dict
    :path schema: Field path
    :path schema: string

    """
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
