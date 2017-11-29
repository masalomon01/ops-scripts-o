# -*- coding: utf-8 -*-
import cookielib
import urllib2
import base64
import json
from urllib import urlencode
import datetime
import re

class Repository(object):
    name = None
    scm = "hg"
    is_private = False
    def __init__(self, api, username, repository, data=None):
        self.api = api
        self.url = 'repositories/%s/%s/' % (username, repository)
        if data is not None:
            for i in data:
                if i not in ['last_updated', 'created_on']:
                    setattr(self, i, data[i])
                else:
                    date = Repository.get_date(data, i)
                    setattr(self, i, date)

    def __repr__(self):
        return "<Repository: %s>" % self.name

    @staticmethod
    def get_date(data, i):
        def convert_date(d):
            return datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S")

        def fix_date(d):
            ''' Remove 'T' in the middle and milliseconds from end, as Bitbucket changed dates on us:
                https://bitbucket.org/site/master/issue/8244/api-repositories-user-repo-date-fields '''
            d = re.sub(r'(\d)T(\d)', r'\1 \2', d)
            return re.sub(r'\.(\d{3})$', r'', d)
        
        try:
            date = convert_date(data[i])
        except Exception:
            try:
                # Failed - try to fix
                d = fix_date(data[i])
                date = convert_date(d)
            except Exception:
                # Just insert raw string
                date = i
        return date

    def get_issues(self):
        if self.has_issues:
            return self.api.get_issues(self.owner, self.slug)

    def get_changesets(self, limit=15):
        return self.api.get_changesets(self.owner, self.slug, limit)

    def get_changeset(self, changeset):
        return self.api.get_changeset(self.owner, self.slug, changeset)

    def get_file(self, filename, revision="tip"):
        return self.api.get_file(self.owner, self.slug, filename, revision)

    def new_issue(self):
        return self.api.new_issue(self.owner, self.slug)

class BBFile(object):
    # Additional functionality will be added to this class in the future.  For now it is a placeholder class.
    def __init__(self, api, username, repository, rev, data):
        self.url = 'repositories/%s/%s/raw/%s/%s' % (username, repository, rev, data['file'])
        # Python variables "type" and "file" are reserved, and incompatible with the BB API ones.
        # Any suggestions on other names are welcome, but I believe "action" and "filename" suit it well.
        self.action = data['type']
        self.filename = data['file']
        self.api = api
        self._handler = None

    def __repr__(self):
        return "<BBFile: %s>" % self.filename

    def __getattr__(self, name):
        if name == 'handler':
            if self._handler == None:
                self._handler = self.api.get_raw(self.url)
            return self._handler
        raise AttributeError

    def read(self, size=-1):
        return self.handler.read(size)

    def readline(self, size=-1):
        return self.handler.readline(size)

class Changeset(object):
    def __init__(self, api, username, repository, data):
        for i in data:
            if i not in ['files', 'timestamp']:
                setattr(self, i, data[i])
        self.timestamp = datetime.datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")
        self.files = []
        for f in data['files']:
            self.files.append(BBFile(api, username, repository, data['node'], f))

    def __repr__(self):
        return "<Changeset: %s>" % self.node

class Issue(object):
    title = ""
    content = ""
    component = None
    milestone = None
    version = None
    responsible = None
    issue_id = None
    priority = "major"
    status = "new"
    kind = "bug"
    created_date = '' # added
    updated_date = '' # added
    def __init__(self, api, username, repository, data=None):
        self.api = api
        self.responsible = username
        self.url = 'repositories/%s/%s/issues' % (username, repository)
        if data:
            self.url = 'repositories/%s/%s/issues/%s' % (username, repository, data['local_id'])
            self.title = data['title']
            self.content = data['content']
            self.component = data['metadata']['component']
            self.milestone = data['metadata']['milestone']
            self.version = data['metadata']['version']
            self.created_date = data['utc_created_on'] # added
            self.updated_date = data['utc_last_updated'] # added
            try:
                self.responsible = data['responsible']['username']
            except KeyError:
                self.responsible = None
            self.priority = data['priority']
            self.status = data['status']
            self.kind = data['metadata']['kind']
            self.issue_id = data['local_id']

    def __repr__(self):
        return "<Issue: %s>" % self.title

    def as_dict(self):
        data = {'title':self.title, 'content':self.content, 'priority':self.priority, 'status':self.status, 'kind':self.kind}
        # At the moment bitbucket doesn't like sending None as responsible
        # The downside is we can't now set responsible to None
        if self.responsible:
            data.update({'responsible':self.responsible})
        if self.component:
            data.update({'component':self.component})
        if self.milestone:
            data.update({'milestone':self.milestone})
        if self.version:
            data.update({'version':self.version})
        return data

    def save(self):
        self.json = self.api.post(self.url, self.as_dict())
        return self.json
    
    def update(self):
        data = self.as_dict()
        data.update({'issue_id' : self.issue_id})
        self.json = self.api.put(self.url, data)
        return self.json

    def add_comment(self, content):
        if not self.issue_id:
            raise ValueError("Needs to be an existing issue!")
        
        data = {"content" : content}
        self.api.post(self.url + "comments", data)


class API(object):
    api_url = 'https://api.bitbucket.org/1.0/'
    count = 0 # added so it can keep track of how many we have

    def __init__(self, username, password, proxy=None):
        encodedstring = base64.encodestring("%s:%s" % (username, password))[:-1]
        self._auth = "Basic %s" % encodedstring
        self._opener = self._create_opener(proxy)

    def _create_opener(self, proxy=None):
        cj = cookielib.LWPCookieJar()
        cookie_handler = urllib2.HTTPCookieProcessor(cj)
        if proxy:
            proxy_handler = urllib2.ProxyHandler(proxy)
            opener = urllib2.build_opener(cookie_handler, proxy_handler)
        else:
            opener = urllib2.build_opener(cookie_handler)
        return opener

    def _raw_request(self, url, **kwargs):
        data = kwargs.get('data')
        request_class = kwargs.get('request', urllib2.Request)
        query_url = self.api_url + url
        if data:
            data = urlencode(data)
        try:
            req = request_class(query_url, data, {"Authorization": self._auth })
            handler = self._opener.open(req)
        except urllib2.HTTPError, e:
            print e.headers
            raise e
        return handler

    def _request(self, url, **kwargs):
        return json.load(self._raw_request(url, **kwargs))

    def post(self, url, data):
        return self._request(url, data=data)

    def put(self, url, data):

        class PutRequest(urllib2.Request):
            def get_method(self):
                return "PUT"

        return self._request(url, data=data, request=PutRequest)


    def get(self, url):
        return self._request(url)

    def get_raw(self, url):
        return self._raw_request(url, None)

    def get_issues(self, username, repository, start, limit): # changed paramaters
        json = self.get('repositories/%s/%s/issues?start=%d&limit=%d' % (username, repository, start, limit)) # changed in order to add the limit. Defaulting to 15
        issues = []
        self.count = json['count'] # added; getting the total number of issues
        for i in json['issues']:
            issue = Issue(self, username, repository, i)
            issues.append(issue)
        return issues

    def get_issue(self, username, repository, issue): # added. Not using right now but could be implemented for future use.
        json = self.get('repositories/%s/%s/issues/%d' % (username, repository, issue)) # pass in the ticket number.
        return Issue(self, username, repository, json)

    def new_issue(self, username, repository, data=None): # https://bitbucket.org/api/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}
        return Issue(self, username, repository, data)

    def get_changesets(self, username, repository, limit=15):
        json = self.get('repositories/%s/%s/changesets?limit=%s' % (username, repository, limit))
        changesets = []
        for i in json['changesets']:
            changesets.append(Changeset(self, username, repository, i))
        return changesets

    def get_changeset(self, username, repository, changeset):
        json = self.get('repositories/%s/%s/changesets/%s' % (username, repository, changeset))
        return Changeset(self, username, repository, json)

    def get_file(self, username, repository, filename, revision="tip"):
        return BBFile(self, username, repository, revision, {'type':'source', 'file':filename})

    def get_repository(self, username, repository):
        json = self.get('repositories/%s/%s/' % (username, repository))
        return Repository(self, username, repository, json)

    def get_repositories(self, username=None):
        repos = []
        if username == None:
            json = self.get('user/repositories/')
            for repo in json:
                repos.append(self.get_repository(repo['owner'], repo['slug']))
        else:
            repo_list = self.get('users/%s/' % username)['repositories']
            for repo in repo_list:
                repos.append(self.get_repository(username, repo['slug']))
        return repos