# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module containing pack related utility functions.
"""

import os
import glob
import json

import yaml

__all__ = [
    'get_pack_list',
    'get_pack_metadata',
    'get_pack_resources'
]

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../../packs'))

PARSER_FUNCS = {
    '.json': json.loads,
    '.yml': yaml.safe_load,
    '.yaml': yaml.safe_load
}

PACK_ICON_URL = 'https://raw.githubusercontent.com/StackStorm/st2contrib/master/packs/%(name)s/icon.png'
NO_PACK_ICON_URL = 'https://raw.githubusercontent.com/StackStorm/st2contrib/master/packs/st2/icon.png'


def get_pack_list():
    packs = os.listdir(PACKS_DIR)
    packs = sorted(packs)
    return packs


def get_pack_metadata(pack):
    metadata_path = os.path.join(PACKS_DIR, pack, 'pack.yaml')
    with open(metadata_path, 'r') as fp:
        content = fp.read()

    metadata = yaml.safe_load(content)

    icon_path = os.path.join(PACKS_DIR, pack, 'icon.png')
    if os.path.exists(icon_path):
        metadata['icon_url'] = PACK_ICON_URL % {'name': pack}
    else:
        metadata['icon_url'] = NO_PACK_ICON_URL

    return metadata


def get_pack_resources(pack):
    sensors_path = os.path.join(PACKS_DIR, pack, 'sensors/')
    actions_path = os.path.join(PACKS_DIR, pack, 'actions/')

    sensor_metadata_files = glob.glob(sensors_path + '/*.json')
    sensor_metadata_files += glob.glob(sensors_path + '/*.yaml')
    sensor_metadata_files += glob.glob(sensors_path + '/*.yml')

    action_metadata_files = glob.glob(actions_path + '/*.json')
    action_metadata_files += glob.glob(actions_path + '/*.yaml')
    action_metadata_files += glob.glob(actions_path + '/*.yml')

    resources = {
        'sensors': [],
        'actions': []
    }

    for sensor_metadata_file in sensor_metadata_files:
        file_name, file_ext = os.path.splitext(sensor_metadata_file)

        with open(sensor_metadata_file, 'r') as fp:
            content = fp.read()

        content = PARSER_FUNCS[file_ext](content)
        item = {
            'name': content['class_name'],
            'description': content.get('description', None)
        }
        resources['sensors'].append(item)

    for action_metadata_file in action_metadata_files:
        file_name, file_ext = os.path.splitext(action_metadata_file)

        with open(action_metadata_file, 'r') as fp:
            content = fp.read()

        content = PARSER_FUNCS[file_ext](content)

        if 'name' not in content:
            continue

        item = {
            'name': content['name'],
            'description': content.get('description', None),
            'runner_type': content.get('runner_type', None),
            'entry_point': content.get('entry_point', None),
            'parameters': content.get('parameters', {})
        }
        resources['actions'].append(item)

    resources['sensors'] = sorted(resources['sensors'], key=lambda i: i['name'])
    resources['actions'] = sorted(resources['actions'], key=lambda i: i['name'])

    return resources
