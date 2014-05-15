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
            raise Exception('Invalid credentials or Genesis url')

        self.sessionid = r.cookies['sessionid']
        self.csrftoken = r.cookies['csrftoken']

    def __call__(self, r):
        # modify and return the request
        r.headers['Cookie'] = 'csrftoken={}; sessionid={}'.format(self.csrftoken, self.sessionid)
        return r


class GenCloud(object):

    """Python API for the Genesis platform."""

    cache = {'data': {}}

    class GenProject(object):

        def __init__(self, data=None, api=None):
            if data:
                for field in data:
                    setattr(self, field, data[field])

            self.api = api
            self.data = None

        def _fetch_data(self):
            if not self.data:
                self.data = []
                data = self.api.data.get(case_ids__contains=self.id)['objects']
                for d in data:
                    if d['id'] not in GenCloud.cache['data']:
                        GenCloud.cache['data'][d['id']] = d
                    else:
                        # TODO: update existing object
                        pass

                    self.data.append(GenCloud.cache['data'][d['id']])

            return self.data

        def data_types(self):
            self._fetch_data()
            return sorted(set(d['type'] for d in self.data))

        def objects(self, **query):
            raise NotImplementedError()

        def find(self, filter):
            raise NotImplementedError()

    def __init__(self, username, password, url='http://cloud.genialis.com'):
        GenCloud.api = slumber.API(urlparse.urljoin(url, 'api/v1/'),
            auth=GenAuth(username, password, url))

    def projects(self):
        if 'projects' not in GenCloud.cache:
            GenCloud.cache['projects'] = {c['id']: GenCloud.GenProject(c, self.api) for c in self.api.case.get()['objects']}

        return GenCloud.cache['projects']

    def get_data(self, objects, field):
        raise NotImplementedError()
