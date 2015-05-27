"""Genesis"""
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import re
import sys
import uuid

if sys.version_info < (3, ):
    import urlparse
else:
    from urllib import parse as urlparse

import requests
import slumber

from .data import GenData
from .project import GenProject
from .utils import find_field, iterate_schema


CHUNK_SIZE = 10000
DEFAULT_EMAIL = 'anonymous@genialis.com'
DEFAULT_PASSWD = 'anonymous'
DEFAULT_URL = 'https://dictyexpress.research.bcm.edu'


class Genesis(object):

    """Python API for the Genesis platform."""

    def __init__(self, email=DEFAULT_EMAIL, password=DEFAULT_PASSWD, url=DEFAULT_URL):
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

    def project_data(self, project):
        """Return a list of Data objects for given project.

        :param project: ObjectId or slug of Genesis project
        :type project: string
        :rtype: list of Data objects

        """
        projobjects = self.cache['project_objects']
        objects = self.cache['objects']
        project_id = str(project)

        if not re.match('^[0-9a-fA-F]{24}$', project_id):
            # project_id is a slug
            projects = self.api.case.get(url_slug=project_id)['objects']
            if len(projects) != 1:
                raise ValueError(msg='Attribute project not a slug or ObjectId: {}'.format(project_id))

            project_id = str(projects[0]['id'])

        if project_id not in projobjects:
            projobjects[project_id] = []
            data = self.api.data.get(case_ids__contains=project_id)['objects']
            for d in data:
                _id = d['id']
                if _id in objects:
                    # Update existing object
                    objects[_id].update(d)
                else:
                    # Insert new object
                    objects[_id] = GenData(d, self)

                projobjects[project_id].append(objects[_id])

            # Hydrate reference fields
            for d in projobjects[project_id]:
                while True:
                    ref_annotation = {}
                    remove_annotation = []
                    for path, ann in d.annotation.items():
                        if ann['type'].startswith('data:'):
                            # Referenced data object found
                            # Copy annotation
                            if ann['value'] in self.cache['objects']:
                                annotation = self.cache['objects'][ann['value']].annotation
                                ref_annotation.update({path + '.' + k: v for k, v in annotation.items()})

                            remove_annotation.append(path)
                    if ref_annotation:
                        d.annotation.update(ref_annotation)
                        for path in remove_annotation:
                            del d.annotation[path]
                    else:
                        break

        return projobjects[project_id]

    def data(self, **query):
        """Query for Data object annotation."""
        objects = self.cache['objects']
        data = self.api.data.get(**query)['objects']
        data_objects = []

        for d in data:
            _id = d['id']
            if _id in objects:
                # Update existing object
                objects[_id].update(d)
            else:
                # Insert new object
                objects[_id] = GenData(d, self)

            data_objects.append(objects[_id])

        # Hydrate reference fields
        for d in data_objects:
            count += 1
            while True:
                ref_annotation = {}
                remove_annotation = []
                for path, ann in d.annotation.items():
                    if ann['type'].startswith('data:'):
                        # Referenced data object found
                        # Copy annotation
                        _id = ann['value']
                        if _id not in objects:
                            try:
                                d_tmp = self.api.data(_id).get()
                            except slumber.exceptions.HttpClientError as ex:
                                if ex.response.status_code == 404:
                                    continue
                                else:
                                    raise ex

                            objects[_id] = GenData(d_tmp, self)

                        annotation = objects[_id].annotation
                        ref_annotation.update({path + '.' + k: v for k, v in annotation.items()})
                        remove_annotation.append(path)
                if ref_annotation:
                    d.annotation.update(ref_annotation)
                    for path in remove_annotation:
                        del d.annotation[path]
                else:
                    break

        return data_objects

    def processors(self, processor_name=None):
        """Return a list of Processor objects.

        :param project_id: ObjectId of Genesis project
        :type project_id: string
        :rtype: list of Processor objects

        """
        if processor_name:
            return self.api.processor.get(name=processor_name)['objects']
        else:
            return self.api.processor.get()['objects']

    def print_upload_processors(self):
        """Print all upload processor names."""
        for p in self.processors():
            if p['name'].startswith('import:upload:'):
                print(p['name'])

    def print_processor_inputs(self, processor_name):
        """Print processor input fields and types.

        :param processor_name: Processor object name
        :type processor_name: string

        """
        p = self.processors(processor_name=processor_name)

        if len(p) == 1:
            p = p[0]
        else:
            Exception('Invalid processor name')

        for field_schema, _, _ in iterate_schema({}, p['input_schema'], 'input'):
            name = field_schema['name']
            typ = field_schema['type']
            # value = fields[name] if name in fields else None
            print("{} -> {}".format(name, typ))

    def rundata(self, strjson):
        """POST JSON data object to server"""

        d = json.loads(strjson)
        return self.api.data.post(d)

    def create(self, data, resource='data'):
        """Create an object of resource:

        * data
        * project
        * processor
        * trigger
        * template

        :param data: Object values
        :type data: dict
        :param resource: Resource name
        :type resource: string

        """
        if isinstance(data, dict):
            data = json.dumps(data)

        if not isinstance(data, str):
            raise ValueError(mgs='data must be dict, str or unicode')

        resource = resource.lower()
        if resource not in ('data', 'project', 'processor', 'trigger', 'template'):
            raise ValueError(mgs='resource must be data, project, processor, trigger or template')

        if resource == 'project':
            resource = 'case'

        url = urlparse.urljoin(self.url, '/api/v1/{}/'.format(resource))
        return requests.post(url,
                             data=data,
                             auth=self.auth,
                             headers={
                                 'cache-control': 'no-cache',
                                 'content-type': 'application/json',
                                 'accept': 'application/json, text/plain, */*',
                                 'referer': self.url,
                             })

    def upload(self, project_id, processor_name, **fields):
        """Upload files and data objects.

        :param project_id: ObjectId of Genesis project
        :type project_id: string
        :param processor_name: Processor object name
        :type processor_name: string
        :param fields: Processor field-value pairs
        :type fields: args
        :rtype: HTTP Response object

        """
        p = self.processors(processor_name=processor_name)

        if len(p) == 1:
            p = p[0]
        else:
            Exception('Invalid processor name {}'.format(processor_name))

        for field_name, field_val in fields.items():
            if field_name not in p['input_schema']:
                Exception("Field {} not in processor {} inputs".format(field_name, p['name']))

            if find_field(p['input_schema'], field_name)['type'].startswith('basic:file:'):
                if not os.path.isfile(field_val):
                    Exception("File {} not found".format(field_val))

        inputs = {}

        for field_name, field_val in fields.items():
            if find_field(p['input_schema'], field_name)['type'].startswith('basic:file:'):

                file_temp = self._upload_file(field_val)

                if not file_temp:
                    Exception("Upload failed for {}".format(field_val))

                inputs[field_name] = {
                    'file': field_val,
                    'file_temp': file_temp
                }
            else:
                inputs[field_name] = field_val

        d = {
            'status': 'uploading',
            'case_ids': [project_id],
            'processor_name': processor_name,
            'input': inputs,
        }

        return self.create(d)

    def _upload_file(self, fn):
        """Upload a single file on the platform.

        File is uploaded in chunks of 1,024 bytes.

        :param fn: File path
        :type fn: string

        """
        size = os.path.getsize(fn)
        counter = 0
        base_name = os.path.basename(fn)
        session_id = str(uuid.uuid4())

        with open(fn, 'rb') as f:
            while True:
                response = None
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                for i in range(5):
                    content_range = 'bytes {}-{}/{}'.format(counter * CHUNK_SIZE,
                                                            counter * CHUNK_SIZE + len(chunk) - 1, size)
                    if i > 0 and response is not None:
                        print("Chunk upload failed (error {}): repeating {}"
                              .format(response.status_code, content_range))

                    response = requests.post(urlparse.urljoin(self.url, 'upload/'),
                                             auth=self.auth,
                                             data=chunk,
                                             headers={
                                                 'Content-Disposition': 'attachment; filename="{}"'.format(base_name),
                                                 'Content-Length': size,
                                                 'Content-Range': content_range,
                                                 'Content-Type': 'application/octet-stream',
                                                 'Session-Id': session_id})

                    if response.status_code in [200, 201]:
                        break
                else:
                    # Upload of a chunk failed (5 retries)
                    return None

                progress = 100. * (counter * CHUNK_SIZE + len(chunk)) / size
                sys.stdout.write("\r{:.0f} % Uploading {}".format(progress, fn))
                sys.stdout.flush()
                counter += 1
        print()
        return session_id

    def download(self, data_objects, field):
        """Download files of data objects.

        :param data_objects: Data object ids
        :type data_objects: list of UUID strings
        :param field: Download field name
        :type field: string
        :rtype: generator of requests.Response objects

        """
        if not field.startswith('output'):
            raise ValueError("Only processor results (output.* fields) can be downloaded")

        for o in data_objects:
            o = str(o)
            if re.match('^[0-9a-fA-F]{24}$', o) is None:
                raise ValueError("Invalid object id {}".format(o))

            if o not in self.cache['objects']:
                self.cache['objects'][o] = GenData(self.api.data(o).get(), self)

            if field not in self.cache['objects'][o].annotation:
                raise ValueError("Download field {} does not exist".format(field))

            ann = self.cache['objects'][o].annotation[field]
            if ann['type'] != 'basic:file:':
                raise ValueError("Only basic:file: field can be downloaded")

        for o in data_objects:
            ann = self.cache['objects'][o].annotation[field]
            url = urlparse.urljoin(self.url, 'data/{}/{}'.format(o, ann['value']['file']))
            yield requests.get(url, stream=True, auth=self.auth)


class GenAuth(requests.auth.AuthBase):

    """Attach HTTP Genesis Authentication to Request object."""

    def __init__(self, email=DEFAULT_EMAIL, password=DEFAULT_PASSWD, url=DEFAULT_URL):
        payload = {
            'email': email,
            'password': password
        }

        try:
            request = requests.post(url + '/user/ajax/login/', data=payload)
        except requests.exceptions.ConnectionError:
            raise Exception('Server not accessible on {}'.format(url))

        if request.status_code == 403:
            raise Exception('Invalid credentials.')

        if not ('sessionid' in request.cookies and 'csrftoken' in request.cookies):
            raise Exception('Invalid credentials.')

        self.sessionid = request.cookies['sessionid']
        self.csrftoken = request.cookies['csrftoken']
        self.subscribe_id = str(uuid.uuid4())

    def __call__(self, request):
        # modify and return the request
        request.headers['Cookie'] = 'csrftoken={}; sessionid={}'.format(self.csrftoken, self.sessionid)
        request.headers['X-CSRFToken'] = self.csrftoken

        # Not needed until we support HTTP Push with the API
        # if r.path_url != '/upload/':
        #     r.headers['X-SubscribeID'] = self.subscribe_id
        return request
