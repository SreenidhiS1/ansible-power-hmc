#!/usr/bin/python

# Copyright: (c) 2018- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vios_rules
author:
    - Sreenidhi S (@SreenidhiS1)
short_description: Manages and deploys device setting rules on the Virtual I/O Server (VIOS).
notes:
    - All Operations support passwordless authentication.
description:
    - Captures, deploys, imports, lists, compares, adds, modifies, and deletes VIOS device setting rules.
    - Leverages AIX Run Time Expert Solution (ARTEX) technology via the VIOS C(rules) command.
    - VIOS provides predefined default rules containing critical rules for VIOS device configuration
      recommended for VIOS best practice.
version_added: 1.0.0
requirements:
    - Python >= 3.9
options:
    hmc_host:
        description:
            - The IP Address or hostname of the HMC.
        required: true
        type: str
    hmc_auth:
        description:
            - Username and Password credential of the HMC.
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - Username of the HMC to login.
                required: true
                type: str
            password:
                description:
                    - Password of the HMC.
                type: str
    system_name:
        description:
            - The name or MTMS (machine type model serial) of the managed system.
        required: true
        type: str
    vios_name:
        description:
            - The name of the Virtual I/O Server.
        required: true
        type: str
    state:
        description:
            - C(capture) captures the current system configuration on the VIOS. If current rules exist,
              the new captured configuration overwrites them; otherwise, factory default rules are used
              as a template.
            - C(deploy) applies the recommended factory default rules or current rules on the VIOS.
              If no current rules exist, a new rules file is created based on current system settings.
              The new setting does not take effect until system reboot.
            - C(import) imports a user-specified rules file to VIOS current rules. Use I(rules_file) to
              specify the file. Use I(force) to skip ioslevel compatibility checking.
            - C(rule_list) lists and views the rules file contents or system configuration based on the rules template.
            - C(diff) lists the mismatch devices and attributes. Use I(show_count) to show the number of
              differences numerically, and I(system_settings) to include the current system settings.
            - C(add) adds a new rule to the VIOS current rules or a user-specified rules file.
              Either I(device_instance) or I(device_type) must be specified along with I(attribute).
            - C(modify) modifies an existing rule from the current rules or user-specified rules file.
              Either I(device_instance) or I(device_type) must be specified along with I(attribute).
            - C(delete) deletes a rule from current rules or a user-specified rules file.
              Either I(device_instance) or I(device_type) must be specified along with I(attribute).
        type: str
        required: true
        choices: ['capture', 'deploy', 'import', 'rule_list', 'diff', 'add', 'modify', 'delete']
    device_instance:
        description:
            - The device instance name used to search for the device type (class/subclass/type) in ODM.
            - Mutually exclusive with I(device_type).
            - Required for C(add), C(modify), and C(delete) states when I(device_type) is not specified.
        type: str
    device_type:
        description:
            - The device class/subclass/type string used to specify the device.
            - Mutually exclusive with I(device_instance).
            - Required for C(add), C(modify), and C(delete) states when I(device_instance) is not specified.
        type: str
    attribute:
        description:
            - The attribute and optional value pair for the device rule, in the form C(attribute=value)
              or C(attribute) (value optional for C(delete)).
            - Required for C(add), C(modify), and C(delete) states.
        type: str
    default_rules:
        description:
            - When C(true), operates on the factory default rules instead of the current rules.
            - Valid for C(deploy), C(list), and C(diff) states.
        type: bool
    show_count:
        description:
            - When C(true), shows the number of differences numerically.
            - Valid for the C(diff) state only.
        type: bool
    system_settings:
        description:
            - When C(true), includes current system settings in the output.
            - Valid for C(list) and C(diff) states.
        type: bool
    rules_file:
        description:
            - Path to a user-specified rules file on the VIOS.
            - Valid for C(import), C(list), C(diff), C(add), C(modify), and C(delete) states.
        type: str
    force:
        description:
            - When C(true), forces the C(import) operation to continue even if non-fatal errors
              are encountered (e.g. ioslevel incompatibility).
            - Valid for the C(import) state only.
        type: bool
'''

EXAMPLES = '''
- name: Capture current VIOS system settings
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    state: capture

- name: Deploy VIOS recommended default rules
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    default_rules: true
    state: deploy

- name: Deploy VIOS current rules
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    state: deploy

- name: Import a user-specified rules file to current rules
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    rules_file: /tmp/user_rules.xml
    state: import

- name: Import rules file and force continue on ioslevel incompatibility
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    rules_file: /tmp/user_rules.xml
    force: true
    state: import

- name: List current rules
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    state: rule_list

- name: List default rules
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    default_rules: true
    state: rule_list

- name: List current system settings
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    system_settings: true
    state: rule_list

- name: Show diff between system settings and current rules
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    system_settings: true
    state: diff

- name: Find the mismatch count between two rules files
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    show_count: true
    rules_file: /tmp/rules1.xml
    state: diff

- name: Add a new rule by device type
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    device_type: disk/vscsi/cvdisk
    attribute: queue_depth=8
    state: add

- name: Add reserve_policy rule by device instance
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    device_instance: hdisk0
    attribute: reserve_policy=no_reserve
    state: add

- name: Modify a rule by device type
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    device_type: adapter/pciex/df1000fe
    attribute: num_cmd_elems=2048
    state: modify

- name: Delete a rule by device type
  ibm.power_hmc.vios_rules:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth: "{{ hmc_auth }}"
    system_name: <sys>
    vios_name: <vios>
    device_type: disk/vscsi/cvdisk
    attribute: queue_depth
    state: delete
'''

RETURN = '''
rules_info:
    description: Output from the VIOS rules command. For C(list) and C(diff) states this is a list
                 of lines. For C(capture), C(deploy), C(import), C(add), C(modify), and C(delete)
                 states this reflects any informational output returned by the command.
    type: list
    returned: on success of all states
'''

import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
import sys


def init_logger():
    old_umask = os.umask(0o177)
    try:
        logging.basicConfig(
            filename=LOG_FILENAME,
            format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
            level=logging.DEBUG)
    finally:
        os.umask(old_umask)


def validate_parameters(params):
    opr = params['state']

    mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']
    unsupportedList = []

    if opr == 'capture':
        unsupportedList = ['device_instance', 'device_type', 'attribute',
                           'default_rules', 'show_count', 'system_settings',
                           'rules_file', 'force']

    elif opr == 'deploy':
        unsupportedList = ['device_instance', 'device_type', 'attribute',
                           'show_count', 'system_settings', 'rules_file', 'force']

    elif opr == 'import':
        unsupportedList = ['device_instance', 'device_type', 'attribute',
                           'default_rules', 'show_count', 'system_settings']

    elif opr == 'rule_list':
        unsupportedList = ['device_instance', 'device_type', 'attribute',
                           'show_count', 'force']
        if params['default_rules'] and params['system_settings']:
            raise ParameterError("'default_rules' and 'system_settings' are mutually exclusive")

    elif opr == 'diff':
        unsupportedList = ['device_instance', 'device_type', 'attribute', 'force']
        if params['default_rules'] and params['system_settings']:
            raise ParameterError("'default_rules' and 'system_settings' are mutually exclusive")

    elif opr in ('add', 'modify', 'delete'):
        unsupportedList = ['default_rules', 'show_count', 'system_settings', 'force']
        if params['rules_file'] is None:
            pass  # rules_file is optional for add/modify/delete
        if params['device_instance'] is None and params['device_type'] is None:
            raise ParameterError("either 'device_instance' or 'device_type' must be specified")
        if params['device_instance'] is not None and params['device_type'] is not None:
            raise ParameterError("'device_instance' and 'device_type' are mutually exclusive")
        if params['attribute'] is None:
            raise ParameterError("mandatory parameter 'attribute' is missing")

    collate = []
    for eachMandatory in mandatoryList:
        if not params[eachMandatory]:
            collate.append(eachMandatory)
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))

    collate = []
    for eachUnsupported in unsupportedList:
        if params[eachUnsupported]:
            collate.append(eachUnsupported)
    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (', '.join(collate)))

    if opr == 'import' and params['rules_file'] is None:
        raise ParameterError("mandatory parameter 'rules_file' is missing for import operation")


def _setup_hmc(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    return hmc_conn, hmc


def _check_system_and_vios(module, hmc_conn, params):
    system_name = params['system_name']
    vios_name = params['vios_name']
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines()
        + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if system_name not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    vios_list = hmc_conn.execute(
        "lssyscfg -r lpar -m {0} -F name".format(system_name)
    ).splitlines()
    if vios_name not in vios_list:
        module.fail_json(msg="The vios is not available in the managed system")


def capture(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return True, output, None


def deploy(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return True, output, None


def import_rules(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return True, output, None


def list_rules(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return False, output, None


def diff_rules(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return False, output, None


def add_rule(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return True, output, None


def modify_rule(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return True, output, None


def delete_rule(module, params):
    validate_parameters(params)
    hmc_conn, hmc = _setup_hmc(module, params)
    _check_system_and_vios(module, hmc_conn, params)
    cmd = hmc.create_rules_command(params)
    result = hmc.runCommandOnVIOS(params['system_name'], params['vios_name'], cmd, True)
    output = result.splitlines() if result else []
    return True, output, None


def perform_task(module):
    params = module.params
    actions = {
        'capture': capture,
        'deploy': deploy,
        'import': import_rules,
        'rule_list': list_rules,
        'diff': diff_rules,
        'add': add_rule,
        'modify': modify_rule,
        'delete': delete_rule,
    }

    if not params['hmc_auth']:
        return False, "missing credential info", None

    try:
        return actions[params['state']](module, params)
    except Exception as error:
        return False, repr(error), None


def run_module():
    module_args = dict(
        hmc_host=dict(type='str', required=True),
        hmc_auth=dict(type='dict',
                      required=True,
                      no_log=True,
                      options=dict(
                          username=dict(required=True, type='str'),
                          password=dict(type='str', no_log=True),
                      )),
        system_name=dict(type='str', required=True),
        vios_name=dict(type='str', required=True),
        state=dict(type='str',
                   required=True,
                   choices=['capture', 'deploy', 'import', 'rule_list',
                            'diff', 'add', 'modify', 'delete']),
        device_instance=dict(type='str'),
        device_type=dict(type='str'),
        attribute=dict(type='str'),
        default_rules=dict(type='bool'),
        show_count=dict(type='bool'),
        system_settings=dict(type='bool'),
        rules_file=dict(type='str'),
        force=dict(type='bool'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('device_instance', 'device_type')],
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json(msg="Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    changed, info, warning = perform_task(module)

    if isinstance(info, str):
        module.fail_json(msg=info)

    result = {}
    result['changed'] = changed
    result['rules_info'] = info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
