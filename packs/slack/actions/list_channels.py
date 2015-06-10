import json
import httplib
import urllib

import requests

from st2actions.runners.pythonrunner import Action

__all__ = [
    'ListChannelsAction'
]


class ListChannelsAction(Action):
    def run(self, token, exclude_archived):
        config = self.config['list_channels_action']
        token = token if token else config['token']
        exclude_archived = exclude_archived if exclude_archived else config['exclude_archived']
        url = 'https://slack.com/api/channels.list'

        headers = {}
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        body = {
            'token': token,
            'exclude_archived': exclude_archived
        }

        data = urllib.urlencode(body)
        response = requests.get(url=url,
                                 headers=headers, params=data)

        results = response.json()

        if results['ok'] == True:
            return results
        else:
            failure_reason = ('Failed to get channel list: %s \
                              (status code: %s)' % (response.text,
                              response.status_code))
            self.logger.exception(failure_reason)
            raise Exception(failure_reason)

        return True
