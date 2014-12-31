#!/usr/bin/env python

import os
import re
import glob
import json
import argparse

import yaml

"""
Script which verifies that pack contains README which meets the following criteria:

1. Readme contains configuration section if config.yaml file exists
2. Readme contains a section for each of the available actions and sensors
"""

CONFIGURATION_SECTION_RE = r'##\s?Configuration'
ACTIONS_SECTION_RE = r'##\s+Actions'
SENSORS_SECTION_RE = r'##\s+Sensors'

PARSER_FUNCS = {
    '.yaml': yaml.safe_load,
    '.json': json.loads
}


def validate_pack_readme(pack_path):
    # TODO: Refactor and make it more modular and re-usable
    pack_path = os.path.abspath(os.path.relpath(pack_path))

    if not os.path.isdir(pack_path):
        raise ValueError('Pack "%s" doesn\'t exist' % (pack_path))

    pack_name = os.path.basename(pack_path)
    readme_path = os.path.join(pack_path, 'README.md')

    if not os.path.isfile(readme_path):
        raise ValueError('Pack "%s" is missing "README.md" file' % (pack_name))

    # TODO: We should use loads hers
    config_path = os.path.join(pack_path, 'config.yaml')
    actions_path = os.path.join(pack_path, 'actions')
    sensors_path = os.path.join(pack_path, 'sensors')

    actions = glob.glob(actions_path + '/*.yaml') + glob.glob(actions_path + '/*.json')
    sensors = glob.glob(sensors_path + '/*.yaml') + glob.glob(sensors_path + '/*.json')

    action_names = []
    sensor_names = []

    # Find exposed actions
    for action_metadata_file in actions:
        extension = os.path.splitext(action_metadata_file)[1]

        with open(action_metadata_file, 'r') as fp:
            content = fp.read()

        parser_func = PARSER_FUNCS[extension]
        parser_func = PARSER_FUNCS[extension]
        action_metadata = parser_func(content)
        action_names.append(action_metadata['name'])

    # Find exposed sensors
    for sensor_metadata_file in sensors:
        extension = os.path.splitext(sensor_metadata_file)[1]

        with open(sensor_metadata_file, 'r') as fp:
            content = fp.read()

        parser_func = PARSER_FUNCS[extension]
        sensor_metadata = parser_func(content)
        sensor_names.append(sensor_metadata['class_name'])

    required_readme_sections = []

    if os.path.isfile(config_path):
        required_readme_sections.append(CONFIGURATION_SECTION_RE)

    # Update required sections based on the available actions and sensors
    if len(action_names) >= 1:
        required_readme_sections.append(ACTIONS_SECTION_RE)

    if len(sensor_names) >= 1:
        required_readme_sections.append(SENSORS_SECTION_RE)

    for action_name in action_names:
        required_section = '%s' % (action_name)
        required_readme_sections.append(required_section)

    for sensor_name in sensor_names:
        required_section = '###\s?%s' % (sensor_name)
        required_readme_sections.append(required_section)

    with open(readme_path, 'r') as fp:
        readme_content = fp.read()

    for section_re in required_readme_sections:
        if re.search(section_re, readme_content) is None:
            raise ValueError('Readme is missing the following section: "%s"' % (section_re))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--pack-path', help='Path to the pack directory')

    args = parser.parse_args()
    validate_pack_readme(pack_path=args.pack_path)
