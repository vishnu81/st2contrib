#!/usr/bin/env python
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
Script which updates README.md with a list of all the available packs.
"""

import os
import copy
import argparse

from utils.pack import get_pack_list
from utils.pack import get_pack_metadata
from utils.pack import get_pack_resources

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKS_DIR = os.path.join(CURRENT_DIR, '../packs')
README_PATH = os.path.join(CURRENT_DIR, '../README.md')


BASE_REPO_URL = 'https://github.com/StackStorm/st2contrib'
BASE_PACKS_URL = 'https://github.com/StackStorm/st2contrib/tree/master/packs'


def generate_pack_list_table(packs):
    lines = []

    lines.append('Icon | Name | Description | Keywords | Author | Latest Version | Available Resources')
    lines.append('---- | ---- | ----------- | -------- | ------ | -------------- | -------------------')

    for pack_name, metadata in packs:
        values = copy.deepcopy(metadata)
        values['base_packs_url'] = BASE_PACKS_URL
        values['base_repo_url'] = BASE_REPO_URL
        values['keywords'] = ', '.join(metadata.get('keywords', []))
        line = '[![%(name)s icon](%(icon_url)s)](%(base_packs_url)s/%(name)s) | [%(name)s](%(base_packs_url)s/%(name)s) | %(description)s | %(keywords)s | [%(author)s](mailto:%(email)s) | %(version)s | [click](%(base_repo_url)s#%(name)s-pack)' % (values)
        lines.append(line)

    result = '\n'.join(lines)
    return result


def generate_pack_resources_tables(packs):
    lines = []

    for pack_name, metadata in packs:
        pack_resources = get_pack_resources(pack=pack_name)
        table = generate_pack_resources_table(pack_name=pack_name,
                                              metadata=metadata,
                                              resources=pack_resources)
        if not table:
            continue

        lines.append(table)

    result = '\n\n'.join(lines)
    return result


def generate_pack_resources_table(pack_name, metadata, resources):
    lines = []

    if not resources['sensors'] and not resources['actions']:
        return None

    lines.append('### %s pack\n' % (pack_name))
    lines.append('![%s icon](%s)' % (pack_name, metadata['icon_url']))
    lines.append('')

    if resources['sensors']:
        lines.append('#### Sensors')
        lines.append('')
        lines.append('Name | Description')
        lines.append('---- | -----------')

        for sensor in resources['sensors']:
            lines.append('%s | %s' % (sensor['name'], sensor['description']))

        if resources['actions']:
            lines.append('')

    if resources['actions']:
        lines.append('#### Actions')
        lines.append('')
        lines.append('Name | Description')
        lines.append('---- | -----------')

        for action in resources['actions']:
            lines.append('%s | %s' % (action['name'], action['description']))

    result = '\n'.join(lines)
    return result


def get_updated_readme(table):
    with open(README_PATH, 'r') as fp:
        current_readme = fp.read()

    head = current_readme.split('## Available Packs\n\n')[0]
    tail = current_readme.split('## License, and Contributors Agreement')[1]

    replacement = '## Available Packs\n\n'
    replacement += table + '\n\n'
    replacement += '## License, and Contributors Agreement'
    updated_readme = head + replacement + tail
    return updated_readme


def main(dry_run):
    packs = get_pack_list()

    packs_with_metadata = []
    for pack in packs:
        try:
            metadata = get_pack_metadata(pack=pack)
        except IOError:
            continue

        packs_with_metadata.append((pack, metadata))

    table1 = generate_pack_list_table(packs=packs_with_metadata)
    table2 = generate_pack_resources_tables(packs=packs_with_metadata)
    table = '%s\n%s' % (table1, table2)
    updated_readme = get_updated_readme(table=table)

    if dry_run:
        print(updated_readme)
    else:
        with open(README_PATH, 'w') as fp:
            fp.write(updated_readme)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--dry-run', help='Print the new readme to stdout',
                        action='store_true', default=False)

    args = parser.parse_args()
    main(dry_run=args.dry_run)
