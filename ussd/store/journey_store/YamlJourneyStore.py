from ussd.store.journey_store import JourneyStore
import os
import yaml
from jinja2 import Template, Environment
from configure import Configuration
from ussd import utilities
from yaml.constructor import ConstructorError
import staticconf
from shutil import rmtree


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


def load_dict_from_yaml(file_path) -> dict:
    file_path = Template(file_path).render(os.environ)
    return Configuration.from_file(
        os.path.abspath(file_path),
        multi_constructors={'!include': include},
        configure=False
    )


def load_yaml(file_path) -> dict:
    if file_path not in staticconf.config.configuration_namespaces:
        yaml_dict = load_dict_from_yaml(file_path)
        staticconf.DictConfiguration(
            yaml_dict,
            namespace=file_path,
            flatten=False)
    return staticconf.config.configuration_namespaces[file_path].configuration_values


class YamlJourneyStore(JourneyStore):
    """
    Loader used for loading and using journeys in a yaml file
    """

    def __init__(self, journey_directory="./.journeys"):
        self.journey_directory = os.path.abspath(journey_directory)

        if not os.path.isdir(self.journey_directory):
            os.makedirs(self.journey_directory)

    def _get_or_create_directory(self, name):
        directory = self._get_directory(name)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        return directory

    def _get_directory(self, name):
        return os.path.join(self.journey_directory, "{0}".format(name))

    def _get_file_path(self, name, version):
        return os.path.join(self._get_directory(name),
                            "{0}.yml".format(version))

    def _get(self, name, version, screen_name, **kwargs):
        if version is None:
            files = os.listdir(self._get_directory(name))
            files.sort()
            version = files[-1]
            if version.replace(".yml", "") == self.edit_mode_version:
                version = files[-2]
            version = version.replace(".yml", "")

        file_path = self._get_file_path(name, version)
        if not os.path.isfile(file_path):
            return None

        journey = load_yaml(file_path)
        if screen_name:
            return journey[screen_name]
        return journey

    def _all(self, name):
        directory = self._get_directory(name)

        if os.path.isdir(directory):
            files = os.listdir(directory)
        else:
            files = []

        results = {}
        for i in files:
            if i.endswith(".yml"):
                version = i.replace(".yml", "")
                results[version] = self._get(name, version, None)
        return results

    def _save(self, name, journey, version):
        file_path = self._get_file_path(name, version)
        if staticconf.config.configuration_namespaces.get(file_path):
            del staticconf.config.configuration_namespaces[file_path]
        self._get_or_create_directory(name)
        with open(file_path, 'w') as outfile:
            yaml.dump(journey, outfile, default_flow_style=False)

    @staticmethod
    def _delete_folder(path):
        rmtree(path)

    def _delete(self, name, version=None):
        directory = self._get_directory(name)
        if version is None:
            self._delete_folder(directory)
        else:
            os.remove(self._get_file_path(name, version))

    def flush(self):
        self._delete_folder(self.journey_directory)
