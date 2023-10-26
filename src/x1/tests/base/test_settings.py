import os
import pathlib
from unittest import mock

import dynaconf


def test_nested_settings():
    data = {"first": {"second": {"third": {"key1": "value1", "key2": False}}}}
    settings = dynaconf.Dynaconf()
    settings.update(data)
    assert isinstance(settings['first'], dict), 'load first level dictionary'
    assert isinstance(settings['first.second'], dict), 'load second level dictionary'
    assert isinstance(settings['first.second.third'], dict), 'load third level dictionary'
    assert settings['first.second.third.key1'] == 'value1', 'load nested str'
    assert settings['first.second.third.key2'] is False, 'load nested bool'

    settings['level1.level2'] = False
    assert isinstance(settings['level1'], dict), 'load first level dictionary, set in runtime'
    assert settings['level1.level2'] is False, 'load nested bool, set in runtime'


FILE1_CONTENT = """
file1_key1: value11
override_in_file: value1
override_in_env: value1
first:
    second1: value1
first_merged:
    second1: value1
first_injected:
    second1: value1
"""

FILE2_CONTENT = """
file2_key1: value21
override_in_file: value2
first:
    second2: value2
first_merged:
    second2: value2
    dynaconf_merge: true
"""


@mock.patch.dict(
    os.environ,
    {
        'TEST_ENV_KEY1': 'value1',
        'TEST_OVERRIDE_IN_ENV': 'value2',
        'TEST_ENV_MAP1': '{foo="bar"}',  # note the TOML format for the value
        'TEST_ENV_MAP2': '@json {"foo": "bar"}',  # note the JSON format and '@json' marker
        'TEST_FIRST_MERGED': '@merge {second3="value3"}',  # note '@merge' marker
        'TEST_FIRST_INJECTED__SECOND2': 'value2',  # note the key 'SECOND2' in uppercase, for Win32
    },
)
def test_override_settings(tmp_path: pathlib.Path):
    file1_path = tmp_path / 'file1.yaml'
    file1_path.write_text(FILE1_CONTENT)
    file2_path = tmp_path / 'file2.yaml'
    file2_path.write_text(FILE2_CONTENT)

    settings = dynaconf.Dynaconf(envvar_prefix='TEST', settings_files=[file1_path, file2_path])

    assert settings['file1_key1'] == 'value11', 'read from file1.yaml'
    assert settings['file2_key1'] == 'value21', 'read from file2.yaml'
    assert settings['env_key1'] == 'value1', 'read from environment'
    assert settings['override_in_file'] == 'value2', 'overridden in file2'
    assert settings['override_in_env'] == 'value2', 'overridden in environment'
    assert settings['first'] == {'second2': 'value2'}, 'map is overridden in file2'
    assert settings['env_map1'] == {'foo': 'bar'}, 'map is defined in environment in TOML'
    assert settings['env_map2'] == {'foo': 'bar'}, 'map is defined in environment in JSON'
    assert settings['first_merged'] == {
        'second1': 'value1',
        'second2': 'value2',
        'second3': 'value3',
    }, 'map is merged using merge markers'
    assert settings['first_injected'] == {
        'second1': 'value1',
        'SECOND2': 'value2',
    }, 'nested key is injected via environment'


def test_merge():
    data1 = {
        "file1_key1": "value11",
        "override_in_file": "value1",
        "override_in_env": "value1",
        "first": {"second1": "value1"},
        "first_merged": {"second1": "value1"},
        "first_injected": {"second1": "value1"},
    }
    data2 = {
        'file2_key1': 'value21',
        'override_in_file': 'value2',
        'first': {'second2': 'value2'},
        'first_merged': {'second2': 'value2', 'dynaconf_merge': 'true'},
    }
    settings = dynaconf.Dynaconf()
    settings.update(data1)
    settings.update(data2, merge=True)

    assert settings['override_in_file'] == 'value2', 'overridden in file2'
    assert settings['first'] == {
        'second1': 'value1',
        'second2': 'value2',
    }, 'map merged from file1, file2'
