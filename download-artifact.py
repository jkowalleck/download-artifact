# download github artifacts from arbitrary ARTIFACTS_URL

from contextlib import closing
from json import loads as json_loads
from os import environ, unlink
from os.path import join
from sys import exit
from tempfile import NamedTemporaryFile
from urllib.request import urlopen, Request
from zipfile import ZipFile

_DEBUG = bool(environ.get('_DLA_DEBUG'))

if _DEBUG:
    print('environ=' + repr(environ), flush=True)
GITHUB_WORKSPACE = str(environ['GITHUB_WORKSPACE'])
GITHUB_TOKEN = str(environ['INPUT_GITHUB_TOKEN'])
ARTIFACTS_URL = str(environ['INPUT_ARTIFACTS_URL'])
ARTIFACT_NAME = str(environ['INPUT_ARTIFACT_NAME'])
DOWNLOAD_PATH = join(GITHUB_WORKSPACE, str(environ['INPUT_DOWNLOAD_PATH']))


class GitHubRequest(Request):
    def __init__(self, url, data=None, headers=None,
                 origin_req_host=None, unverifiable=False,
                 method=None):
        headers = headers or {}
        headers.setdefault('Authorization', 'token ' + GITHUB_TOKEN)
        super().__init__(url, data=data, headers=headers,
                         origin_req_host=origin_req_host, unverifiable=unverifiable,
                         method=method)


try:
    with closing(urlopen(GitHubRequest(ARTIFACTS_URL))) as fp:
        artifacts = json_loads(str(fp.read(), 'utf-8')).get('artifacts', [])
    for artifact in artifacts:
        if _DEBUG:
            print('artifact=' + repr(artifact), flush=True)
        if artifact.get('name') != ARTIFACT_NAME:
            continue
        archive_download_url = artifact.get('archive_download_url')
        if not archive_download_url:
            continue
        if _DEBUG:
            print('archive_download_url=' + repr(archive_download_url), flush=True)
        tfp = NamedTemporaryFile(delete=False)
        try:
            with closing(urlopen(GitHubRequest(archive_download_url))) as fp:
                tfp.write(fp.read())
            tfp.close()
            if _DEBUG:
                print(tfp.name, flush=True)
                print(open(tfp.name, 'r+b').read())
            ZipFile(tfp.name).extractall(DOWNLOAD_PATH)
            exit(0)
        finally:
            unlink(tfp.name)
    raise KeyError('there is no downloadable artifact ' + repr(ARTIFACT_NAME))
except Exception as error:
    print('::error::' + type(error).__name__ + ':' + str(error), flush=True)
    if _DEBUG:
        from logging import Formatter
        print('ERROR: ' + Formatter().formatException((type(error), error, error.__traceback__)), flush=True)
    exit(1)
