import json
import httplib
import urllib

import requests

from st2actions.runners.pythonrunner import Action

__all__ = [
    'ListUsersAction'
]


class ListUsersAction(Action):
    def run(self, token):
        config = self.config['list_users_action']
        token = token if token else config['token']
        url = 'https://slack.com/api/users.list'

        headers = {}
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        body = {
            'token': token
        }

        data = urllib.urlencode(body)
        response = requests.get(url=url,
                                 headers=headers, params=data)

        if response.status_code == httplib.OK:
            return response.json()
        else:
            failure_reason = ('Failed to get user list: %s \
                              (status code: %s)' % (response.text,
                              response.status_code))
            self.logger.exception(failure_reason)
            raise Exception(failure_reason)

        return True
