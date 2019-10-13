import importlib
import os
from datetime import datetime

import yaml
from jinja2 import Template
from yaml.constructor import ConstructorError

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

date_format = "%Y-%m-%d %H:%M:%S.%f"


def str_to_class(import_path):
    module_name, class_name = import_path.rsplit(".", 1)
    try:
        module_ = importlib.import_module(module_name)
        try:
            class_ = getattr(module_, class_name)
        except AttributeError:
            raise Exception('Class does not exist')
    except ImportError:
        raise Exception('Module does not exist')
    return class_


def datetime_to_string(date_obj: datetime):
    return date_obj.strftime(date_format)


def string_to_datetime(date_str_obj: str):
    return datetime.strptime(date_str_obj, date_format)


def get_text(text):
    if type(text) is str:
        return text
    return text['en']


def extract_file(file_name, parent_file_path):
    # first try the raw path

    if os.path.isfile(file_name):
        file_path = file_name
    else:
        file_path = os.path.abspath(
            os.path.join(
                os.path.dirname(parent_file_path),
                file_name
            )
        )
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_name)

    with open(file_path, 'r') as f:
        return yaml.load(f)


def include(loader, node):
    if isinstance(node, yaml.ScalarNode):
        return extract_file(loader.construct_scalar(node), node.start_mark.name)

    elif isinstance(node, yaml.SequenceNode):
        data = {}
        for filename in loader.construct_sequence(node):
            file_path = Template(filename).render(os.environ)
            data.update(extract_file(os.path.abspath(file_path)))

        return data

    else:
        raise ConstructorError("Error:: unrecognised node type in !include statement")



class YamlToGo:
    def __init__(self, file):
        with open(file, 'r') as f:
            data = yaml.load(f)

        included_files = data.get('includes')
        if included_files:
            data.pop('includes', None)
            data.update(included_files)
        self.yaml = data

        self.count = 0

    def get_model_data(self):
        data = {}
        links = []
        for index, value in enumerate(self.yaml):
            data[value] = self.convert_screen(value, index)

        for index, value in enumerate(self.yaml):
            links.extend(self.get_links(value, data))

        data_array = [data.pop('initial_screen')]
        data_array.extend(list(data.values()))

        return {'data': data_array, 'links': links}

    def convert_screen(self, screen, key):
        _data = {}
        name = screen
        screen = self.yaml[screen]
        screen_type = screen['type']
        _data['key'] = key
        _data['title'] = name

        if screen_type == 'initial_screen':
            _data['items'] = [
                {'index': 1, 'portName': 'out1', 'text': 'Initial Screen'}
            ]
        elif screen_type == 'input_screen':
            _data['items'] = [
                {'index': '1', 'portName': 'out1', 'text': get_text(screen['text'])}
            ]
        elif screen_type.endswith('http_screen'):
            _data['items'] = [
                {'index': '1', 'portName': 'out1', 'text': 'Http Request Screen'}
            ]

        elif screen_type == 'menu_screen':
            _data['items'] = []
            for index, value in enumerate(screen['options']):
                _data['items'].append({
                    'index': index + 1,
                    'text': get_text(value['text']),
                    'portName': 'out' + str(index)
                })

        elif screen_type == 'router_screen':
            _data['items'] = []

            for index, value in enumerate(screen['router_options']):
                _data['items'].append({
                    'index': index + 1,
                    'text': value['expression'],
                    'portName': 'out' + str(index)
                })

            if 'default_next_screen' in screen:
                _data['items'].append({
                    'index': len(screen['router_options']) + 1,
                    'text': 'Default Route',
                    'portName': 'outDefault'
                })

        elif screen_type == 'quit_screen':
            _data['items'] = [
                {'index': 1, 'portName': 'out1', 'text': get_text(screen['text'])}
            ]

        return _data

    def get_links(self, screen, data):
        _data = []
        name = screen
        screen = self.yaml[screen]
        screen_type = screen['type']

        if screen_type == 'initial_screen':
            _data = [
                {
                    'from': data[name]['key'],
                    'to': data[screen['next_screen']]['key'],
                    'fromPort': 'out1'
                }
            ]
        elif screen_type == 'input_screen':
            _data = [
                {
                    'from': data[name]['key'],
                    'to': data[screen['next_screen']]['key'],
                    'fromPort': 'out1'
                }
            ]
        elif screen_type.endswith('http_screen'):
            _data = [
                {
                    'from': data[name]['key'],
                    'to': data[screen['next_screen']]['key'],
                    'fromPort': 'out1'
                }
            ]

        elif screen_type == 'menu_screen':
            for index, value in enumerate(screen['options']):
                _data.append({
                    'from': data[name]['key'],
                    'to': data[value['next_screen']]['key'],
                    'fromPort': 'out' + str(index)
                })

        elif screen_type == 'router_screen':
            if 'default_next_screen' in screen:
                _data.append({
                    'from': data[name]['key'],
                    'to': data[screen['default_next_screen']]['key'],
                    'fromPort': 'outDefault'
                })
            for index, value in enumerate(screen['router_options']):
                _data.append({
                    'from': data[name]['key'],
                    'to': data[value['next_screen']]['key'],
                    'fromPort': 'out' + str(index)
                })

        elif screen_type == 'quit_screen':
            pass

        return _data
