import sys
import traceback

from requests.packages.urllib3.exceptions import ReadTimeoutError
import six
import docker

__all__ = [
    'DockerWrapper'
]


class DockerWrapper(object):
    def __init__(self, docker_opts):
        # Assign sane defaults.
        if docker_opts['version'] is None:
            docker_opts['version'] = '1.13'
        if docker_opts['url'] is None:
            docker_opts['url'] = 'unix://var/run/docker.sock'

        self._version = docker_opts['version']
        self._url = docker_opts['url']
        self._timeout = 60
        if docker_opts['timeout'] is not None:
            self._timeout = docker_opts['timeout']
        self._client = docker.Client(base_url=self._url,
                                     version=self._version,
                                     timeout=self._timeout)
        self._docker_build_opts = docker_opts['build_options']

    def build(self, path=None, fileobj=None, tag=None):
        if path is None and fileobj is None:
            raise Exception('Either dir containing dockerfile or path to dockerfile ' +
                            ' must be provided.')
        if path is not None and fileobj is not None:
            sys.stdout.write('Using path to dockerfile: %s\n' % fileobj)
        opts = self._docker_build_opts
        sys.stdout.write('Building docker container. Path = %s, Tag = %s\n' % (path, tag))
        # Depending on docker version, stream may or may not be forced. So let's just always
        # use streaming.
        result = self._client.build(path=path, fileobj=fileobj, tag=tag, quiet=opts['quiet'],
                                    nocache=opts['nocache'], rm=opts['rm'],
                                    stream=True, timeout=opts['timeout'])
        self._print_streamed_result(result)

    def _print_streamed_result(self, result):
        try:
            json_output = six.advance_iterator(result)
            while json_output:
                sys.stdout.write(json_output)
                try:
                    json_output = six.advance_iterator(result)
                except ReadTimeoutError:
                    continue
        except StopIteration:
            pass
        except Exception as e:
            sys.stderr.write(traceback.format_exc())
            sys.stderr.write('Error: %s' % (str(e)))
            raise e

    def push(self, repo, tag=None, insecure_registry=False):
        try:
            for line in self._client.push(repo, tag=tag, insecure_registry=insecure_registry,
                                          stream=True):
                sys.stdout.write(line)
        except Exception as e:
            sys.stderr.write('Error: %s' % (str(e)))
            raise e

    def pull(self, repo, tag=None, insecure_registry=False, auth_config=None):
        try:
            for line in self._client.pull(repo, tag=tag, insecure_registry=insecure_registry,
                                          stream=True, auth_config=auth_config):
                sys.stdout.write(line)
        except Exception as e:
            sys.stderr.write('Error: %s' % (str(e)))
            raise e
