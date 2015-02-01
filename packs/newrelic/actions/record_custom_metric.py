import os
import atexit
import time
import tempfile

import newrelic.agent
import newrelic.core.agent

from st2actions.runners.pythonrunner import Action

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_TEMPLATE_PATH = os.path.join(CURRENT_DIR, 'config.template.ini')


class RecordCustomMetricAction(Action):
    def __init__(self, config=None):
        super(RecordCustomMetricAction, self).__init__(config=config)
        self._initialize_client()

    def run(self, name, value, application=None):
        # TODO: Support for pre-aggregated metrics
        name = 'Custom/' + name

        if application:
            application = newrelic.agent.register_application(name=application)
        else:
            application = newrelic.agent.register_application(name=self.config['app_name'])

        self.logger.info('Recording metric (name=%s, value=%s)' % (name, value))
        newrelic.agent.record_custom_metric(name=name, value=value, application=application)
        time.sleep(30)

        # Force metrics harvest and flush
        agent = newrelic.core.agent.agent_instance()
        agent._run_harvest(shutdown=True)

    def _initialize_client(self):
        # This is awful, but new relic api clients can't be initialized
        # programatically which is even worse so we just use a temporary
        # config file.
        _, temp_path = tempfile.mkstemp(suffix='.ini')

        with open(CONFIG_TEMPLATE_PATH, 'r') as fp:
            config_template = fp.read()

        config_template = config_template.replace('LICENSE-KEY', self.config['api_key'])
        config_template = config_template.replace('APP-NAME', self.config['app_name'])

        with open(temp_path, 'w') as fp:
            fp.write(config_template)

        newrelic.agent.initialize(temp_path)

        @atexit.register
        def delete_temp_config():
            if os.path.exists(temp_path):
                os.remove(temp_path)
