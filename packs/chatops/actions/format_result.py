import jinja2
import json
import six
import os

from st2actions.runners.pythonrunner import Action
from st2client.client import Client

__all__ = [
    'FormatResultAction'
]


def _serialize(data):
    if isinstance(data, dict):
        return '\n'.join(['%s : %s' % (k, v) for k, v in six.iteritems(data)])
    return data


def format_possible_failure_result(result):
    '''
    Error result as generator by the runner container is of the form
    {'message': x, 'traceback': traceback}

    Try and pull out these value upfront. Some other runners that could publish
    these properties would get them for free.
    '''
    output = {}
    message = result.get('message', None)
    if message:
        output['message'] = message
    traceback = result.get('traceback', None)
    if traceback:
        output['traceback'] = traceback
    return output


def format_default_result(result):
    try:
        output = json.loads(result) if isinstance(result, six.string_types) else result
        return _serialize(output)
    except (ValueError, TypeError):
        return result


def format_localrunner_result(result, do_serialize=True):
    output = format_possible_failure_result(result)
    # Add in various properties if they have values
    stdout = result.get('stdout', None)
    if stdout:
        try:
            output['stdout'] = stdout.strip()
        except AttributeError:
            output['stdout'] = stdout
    stderr = result.get('stderr', None)
    if stderr:
        output['stderr'] = stderr.strip()
    return_code = result.get('return_code', 0)
    if return_code != 0:
        output['return_code'] = return_code
    error = result.get('error', None)
    if error:
        output['error'] = error

    return _serialize(output) if do_serialize else output


def format_remoterunner_result(result):
    output = format_possible_failure_result(result)
    output.update({k: format_localrunner_result(v, do_serialize=False)
                   for k, v in six.iteritems(result)})
    return _serialize(output)


def format_actionchain_result(result):
    output = format_possible_failure_result(result)
    return '' if not output else _serialize(output)


def format_mistral_result(result):
    return format_default_result(result)


def format_pythonrunner_result(result):
    output = format_possible_failure_result(result)
    # Add in various properties if they have values
    result_ = result.get('result', None)
    if result_ is not None:
        output['result'] = result_
    stdout = result.get('stdout', None)
    if stdout:
        try:
            output['stdout'] = stdout.strip()
        except AttributeError:
            output['stdout'] = stdout
    stderr = result.get('stderr', None)
    if stderr:
        output['stderr'] = stderr.strip()
    exit_code = result.get('exit_code', 0)
    if exit_code != 0:
        output['exit_code'] = exit_code
    return _serialize(output)


def format_httprunner_result(result):
    return format_default_result(result)


def format_windowsrunner_result(result):
    # same format as pythonrunner
    return format_pythonrunner_result(result)


FORMATTERS = {
    'default': format_default_result,
    # localrunner
    'local-shell-cmd': format_localrunner_result,
    'run-local': format_localrunner_result,
    'local-shell-script': format_localrunner_result,
    'run-local-script': format_localrunner_result,
    # remoterunner
    'remote-shell-cmd': format_remoterunner_result,
    'run-remote': format_remoterunner_result,
    'remote-shell-script': format_remoterunner_result,
    'run-remote-script': format_remoterunner_result,
    # httprunner
    'http-request': format_httprunner_result,
    'http-runner': format_httprunner_result,
    # mistralrunner
    'mistral-v1': format_mistral_result,
    'mistral-v2': format_mistral_result,
    # actionchainrunner
    'action-chain': format_actionchain_result,
    # pythonrunner
    'run-python': format_pythonrunner_result,
    'python-script': format_pythonrunner_result,
    # windowsrunner
    'windows-cmd': format_windowsrunner_result,
    'windows-script': format_windowsrunner_result
}


class FormatResultAction(Action):
    def __init__(self, config):
        super(FormatResultAction, self).__init__(config)
        api_url = os.environ.get('ST2_ACTION_API_URL', None)
        token = os.environ.get('ST2_ACTION_AUTH_TOKEN', None)
        self.client = Client(api_url=api_url, token=token)
        self.jinja = jinja2.Environment()

    def run(self, execution_id):
        context = {
            'FORMATTERS': FORMATTERS
        }

        execution = self.client.liveactions.get_by_id(execution_id)
        context.update({
            'execution': execution
        })

        alias_id = execution.context.get('action_alias_ref', {}).get('id', None)
        if alias_id:
            alias = self.client.managers['ActionAlias'].get_by_id(alias_id)

            context.update({
                'alias': alias
            })

        if alias and alias.result:
            enabled = alias.result.get('enabled', True)

            if enabled and 'format' in alias.result:
                return self.jinja.from_string(alias.result['format']).render(context)
        else:
            path = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(path, 'templates/default.j2'), 'r') as f:
                return self.jinja.from_string(f.read()).render(context)
