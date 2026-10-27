from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_MODULE = "ansible_collections.ibm.power_hmc.plugins.modules.vios_rules"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}

# ---------------------------------------------------------------------------
# Base params dict — every optional key is present (set to None)
# ---------------------------------------------------------------------------
_base = {
    'hmc_host': 'hmc_host',
    'hmc_auth': hmc_auth,
    'system_name': 'sys',
    'vios_name': 'vios',
    'device_instance': None,
    'device_type': None,
    'attribute': None,
    'default_rules': None,
    'show_count': None,
    'system_settings': None,
    'rules_file': None,
    'force': None,
}


def _p(state, **overrides):
    """Return a copy of _base with 'state' set and any overrides applied."""
    d = dict(_base)
    d['state'] = state
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------
test_data_capture = [
    # missing hmc_host
    (_p('capture', hmc_host=None),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # missing system_name
    (_p('capture', system_name=None),
     "ParameterError: mandatory parameter 'system_name' is missing"),

    # missing vios_name
    (_p('capture', vios_name=None),
     "ParameterError: mandatory parameter 'vios_name' is missing"),

    # unsupported parameter: rules_file
    (_p('capture', rules_file='/tmp/r.xml'),
     "ParameterError: unsupported parameter: rules_file"),

    # unsupported parameter: force
    (_p('capture', force=True),
     "ParameterError: unsupported parameter: force"),
]

# ---------------------------------------------------------------------------
# deploy
# ---------------------------------------------------------------------------
test_data_deploy = [
    # missing hmc_host
    (_p('deploy', hmc_host=None),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # unsupported parameter: rules_file
    (_p('deploy', rules_file='/tmp/r.xml'),
     "ParameterError: unsupported parameter: rules_file"),

    # unsupported parameter: force
    (_p('deploy', force=True),
     "ParameterError: unsupported parameter: force"),

    # unsupported parameter: show_count
    (_p('deploy', show_count=True),
     "ParameterError: unsupported parameter: show_count"),
]

# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------
test_data_import = [
    # missing hmc_host
    (_p('import', hmc_host=None),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # missing rules_file
    (_p('import'),
     "ParameterError: mandatory parameter 'rules_file' is missing for import operation"),

    # unsupported parameter: default_rules
    (_p('import', rules_file='/tmp/r.xml', default_rules=True),
     "ParameterError: unsupported parameter: default_rules"),

    # unsupported parameter: show_count
    (_p('import', rules_file='/tmp/r.xml', show_count=True),
     "ParameterError: unsupported parameter: show_count"),

    # unsupported parameter: system_settings
    (_p('import', rules_file='/tmp/r.xml', system_settings=True),
     "ParameterError: unsupported parameter: system_settings"),
]

# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------
test_data_list = [
    # missing hmc_host
    (_p('rule_list', hmc_host=None),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # unsupported parameter: force
    (_p('rule_list', force=True),
     "ParameterError: unsupported parameter: force"),

    # unsupported parameter: show_count
    (_p('rule_list', show_count=True),
     "ParameterError: unsupported parameter: show_count"),

    # mutually exclusive: default_rules and system_settings
    (_p('rule_list', default_rules=True, system_settings=True),
     "ParameterError: 'default_rules' and 'system_settings' are mutually exclusive"),
]

# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------
test_data_diff = [
    # missing hmc_host
    (_p('diff', hmc_host=None),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # unsupported parameter: force
    (_p('diff', force=True),
     "ParameterError: unsupported parameter: force"),

    # mutually exclusive: default_rules and system_settings
    (_p('diff', default_rules=True, system_settings=True),
     "ParameterError: 'default_rules' and 'system_settings' are mutually exclusive"),
]

# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------
test_data_add = [
    # missing hmc_host
    (_p('add', hmc_host=None, device_type='disk/vscsi/cvdisk', attribute='queue_depth=8'),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # missing both device_instance and device_type
    (_p('add', attribute='queue_depth=8'),
     "ParameterError: either 'device_instance' or 'device_type' must be specified"),

    # missing attribute
    (_p('add', device_type='disk/vscsi/cvdisk'),
     "ParameterError: mandatory parameter 'attribute' is missing"),

    # unsupported parameter: default_rules
    (_p('add', device_type='disk/vscsi/cvdisk', attribute='queue_depth=8', default_rules=True),
     "ParameterError: unsupported parameter: default_rules"),

    # unsupported parameter: show_count
    (_p('add', device_type='disk/vscsi/cvdisk', attribute='queue_depth=8', show_count=True),
     "ParameterError: unsupported parameter: show_count"),

    # unsupported parameter: system_settings
    (_p('add', device_type='disk/vscsi/cvdisk', attribute='queue_depth=8', system_settings=True),
     "ParameterError: unsupported parameter: system_settings"),

    # unsupported parameter: force
    (_p('add', device_type='disk/vscsi/cvdisk', attribute='queue_depth=8', force=True),
     "ParameterError: unsupported parameter: force"),
]

# ---------------------------------------------------------------------------
# modify
# ---------------------------------------------------------------------------
test_data_modify = [
    # missing hmc_host
    (_p('modify', hmc_host=None, device_type='disk/fcp/mpioapdisk', attribute='reserve_policy=no_reserve'),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # missing both device_instance and device_type
    (_p('modify', attribute='reserve_policy=no_reserve'),
     "ParameterError: either 'device_instance' or 'device_type' must be specified"),

    # missing attribute
    (_p('modify', device_instance='hdisk0'),
     "ParameterError: mandatory parameter 'attribute' is missing"),

    # unsupported parameter: default_rules
    (_p('modify', device_type='disk/fcp/mpioapdisk', attribute='reserve_policy=no_reserve', default_rules=True),
     "ParameterError: unsupported parameter: default_rules"),
]

# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------
test_data_delete = [
    # missing hmc_host
    (_p('delete', hmc_host=None, device_type='disk/vscsi/cvdisk', attribute='queue_depth'),
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # missing both device_instance and device_type
    (_p('delete', attribute='queue_depth'),
     "ParameterError: either 'device_instance' or 'device_type' must be specified"),

    # missing attribute
    (_p('delete', device_type='disk/vscsi/cvdisk'),
     "ParameterError: mandatory parameter 'attribute' is missing"),

    # unsupported parameter: default_rules
    (_p('delete', device_type='disk/vscsi/cvdisk', attribute='queue_depth', default_rules=True),
     "ParameterError: unsupported parameter: default_rules"),
]


def common_mock_setup(mocker):
    mod = importlib.import_module(IMPORT_MODULE)
    mocker.patch.object(mod, 'HmcCliConnection')
    mocker.patch.object(mod, 'Hmc', autospec=True)
    return mod


@pytest.mark.parametrize("test_input, expectedError", test_data_capture)
def test_capture(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.capture(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.capture(mod, test_input)


@pytest.mark.parametrize("test_input, expectedError", test_data_deploy)
def test_deploy(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.deploy(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.deploy(mod, test_input)


@pytest.mark.parametrize("test_input, expectedError", test_data_import)
def test_import_rules(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.import_rules(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.import_rules(mod, test_input)


@pytest.mark.parametrize("test_input, expectedError", test_data_list)
def test_list_rules(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.list_rules(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.list_rules(mod, test_input)


@pytest.mark.parametrize("test_input, expectedError", test_data_diff)
def test_diff_rules(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.diff_rules(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.diff_rules(mod, test_input)


@pytest.mark.parametrize("test_input, expectedError", test_data_add)
def test_add_rule(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.add_rule(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.add_rule(mod, test_input)


@pytest.mark.parametrize("test_input, expectedError", test_data_modify)
def test_modify_rule(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.modify_rule(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.modify_rule(mod, test_input)


@pytest.mark.parametrize("test_input, expectedError", test_data_delete)
def test_delete_rule(mocker, test_input, expectedError):
    mod = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            mod.delete_rule(mod, test_input)
        assert expectedError == repr(e.value)
    else:
        mod.delete_rule(mod, test_input)
