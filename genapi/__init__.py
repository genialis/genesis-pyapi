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


class GenProject(object):

    def __init__(self, data=None, gencloud=None):
        if data:
            for field in data:
                setattr(self, field, data[field])

        self.gencloud = gencloud

    def data_types(self):
        data = self.gencloud.project_objects(self.id)
        return sorted(set(d['type'] for d in data))

    def objects(self, **query):
        raise NotImplementedError()

    def find(self, filter):
        raise NotImplementedError()


class GenCloud(object):

    """Python API for the Genesis platform."""

    def __init__(self, username, password, url='http://cloud.genialis.com'):
        self.api = slumber.API(urlparse.urljoin(url, 'api/v1/'),
            auth=GenAuth(username, password, url))

        self.cache = {'objects': {}, 'projects': None, 'project_objects': {}}

    def projects(self):
        if not ('projects' in self.cache and self.cache['projects']):
            self.cache['projects'] = {c['id']: GenProject(c, self) for c in self.api.case.get()['objects']}

        return self.cache['projects']

    def project_objects(self, project_id):
        if not self.cache['project_objects'][project_id]:
            self.cache['project_objects'][project_id] = []
            data = self.api.data.get(case_ids__contains=project_id)['objects']
            for d in data:
                if d['id'] not in self.cache['objects']:
                    self.cache['objects'][d['id']] = d
                else:
                    # TODO: update existing object
                    pass

                self.cache['project_objects'][project_id].append(self.cache['objects'][d['id']])

        return self.cache['project_objects'][project_id]

    def get_data(self, objects, field):
        raise NotImplementedError()


g = GenCloud('admin', 'admin', 'http://gendev:10180')
p = g.projects().itervalues().next()
