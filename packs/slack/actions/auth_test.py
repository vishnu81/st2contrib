import json
import httplib
import urllib

import requests

from st2actions.runners.pythonrunner import Action

__all__ = [
    'AuthTestAction'
]


class AuthTestAction(Action):
    def run(self, token):
        config = self.config['auth_test_action']
        token = token if token else config['token']
        url = 'https://slack.com/api/auth.test'

        headers = {}
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        body = {
            'token': token
        }

        data = urllib.urlencode(body)
        response = requests.get(url=url,
                                 headers=headers, params=data)

        results = response.json()

        if results['ok'] == True:
            return results
        else:
            failure_reason = ('Failed to authenticate: %s \
                              (status code: %s)' % (response.text,
                              response.status_code))
            self.logger.exception(failure_reason)
            raise Exception(failure_reason)

        return True
