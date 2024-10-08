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
module: vios_maintenance
author:
    - Sreenidhi S(@SreenidhiS1)
short_description: Manage the vios backup
notes:
    - All Operations support passwordless authentication.
description:
    - Create a VIOS backup file
    - List VIOS backup file details
    - Modify the name of the VIOS backup file
    - Remove a VIOS backup file
    - Restore a VIOS backup
version_added: 1.0.0
options:
    hmc_host:
        description:
            - The IP address or hostname of the HMC.
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
    attributes:
        description:
            - Configuration parameters required for VIOS backup and restore.
        type: dict
        required: true
        suboptions:
            types:
                description:
                    - The type of VIOS backup to create.
                    - Valid values are C(viosioconfig)for a VIOS I/O configuration backup,
                      C(vios) for a full VIOS backup, C(ssp) for a Shared Storage Pool configuration backup.
                type: str
                required: true
                choices: ['vios', 'viosioconfig', 'ssp']
            system:
                description:
                    - The name of the managed system which has the VIOS to backup.
                type: str
            vios_id:
                description:
                    - The ID of the VIOS to backup.
                      vios_id, vios_uuid, vios_name are mutually exclusive.
                type: str
            vios_uuid:
                description:
                    - The UUID of the VIOS to backup.
                      vios_id, vios_uuid, vios_name are mutually exclusive.
                type: str
            vios_name:
                description:
                    - The name of the VIOS to backup.
                      vios_id, vios_uuid, vios_name are mutually exclusive.
                type: str
            backup_name:
                description:
                    - The name of the file where the backup will be saved.
                type: str
            file_list:
                description:
                    - The list of the backup files that needs to be removed.
                      This option is for C(remove) state only.
                      Add backup file name as comma seperated values.
                type: list
                elements: str
            nimol_resource:
                description:
                    - Option to include the NIMOL resources.
                      C(1) to include and C(0) to not include the NIMOL resources.
                      This option is only valid when creating a full VIOS backup.
                type: int
                choices: [1, 0]
            media_repository:
                description:
                    - Option to include the contents of the media repository.
                      C(1) to include and C(0) to not include the media resources.
                      This option is only valid when creating a full VIOS backup.
                type: int
                choices: [1, 0]
            volume_group_structure:
                description:
                    - Option to include the volume groups structure of user.
                      C(1) to include and C(0) to not include the volume groups structure of user.
                      This option is only valid when creating a full VIOS backup.
                type: int
                choices: [1, 0]
            restart:
                description:
                    - Specify this option to restart the VIOS if required.
                      C(True) to restart the VIOS and C(False) not to restart the VIOS.
                      Valid for C(restore) state only.
                type: bool
            new_name:
                description:
                    - The attributes to change the name of the backup file.
                      Valid for C(modify) state only.
                type: str
    state:
        description:
            - C(facts) does not change anything on the HMC and returns list of backup files of a VIOS.
            - C(present) ensures the new backup file is created for the specified VIOS.
            - C(absent) ensures the specified backup file/s is removed from the HMC.
            - C(restore) ensures the backup file is restored.
            - C(modify) ensures that the name of the backup file is changed in HMC.
        type: str
        choices: ['facts', 'present', 'absent', 'restore', 'modify']
'''

EXAMPLES = '''
- name: Create a viosioconfig backup file
  vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    attributes:
        vios_name: <vios name>
        backup_name: test
        system: <sys>
        types: viosioconfig
    state: present

- name: Restore a vios from test backup file
  vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    attributes:
        vios_name: <vios name>
        backup_name: test.tar.gz
        system: <sys>
        types: viosioconfig
    state: restore

- name: Remove a backup file
  vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    attributes:
        vios_name: <vios name>
        backup_name: test.tar.gz
        system: <sys>
        types: viosioconfig
    state: absent

- name: Rename the backup file
  vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    attributes:
        vios_name: <vios name>
        backup_name: test.tar.gz
        new_name: new.tar.gz
        system: <sys>
        types: viosioconfig
    state: modify
'''

RETURN = '''
Command_output:
    description: Respective user configuration
    type: dict
    returned: on success of all states except C(absent)
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
import sys

USER_AUTHORITY_ERR = "HSCL350B The user does not have the appropriate authority"


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def validate_sub_params(params):
    opr = None
    unsupportedList = []
    mandatoryList = []
    opr = params['state']

    if opr == 'update':
        params = params['attributes']
        mandatoryList = ['repository', 'system_name']
    if opr in ['update']:
        count = sum(x is not None for x in [params['vios_id'], params['vios_name']])
        if count == 0:
            raise ParameterError("Missing VIOS details")
        if count != 1:
            raise ParameterError("Parameters 'vios_id' and 'vios_name' are mutually exclusive")
        
    repo = params['repository']
    if repo == 'sftp':
        count = sum(x is not None for x in [params['ssh_key_file'], params['password']])
        if count != 1:
            raise ParameterError("Parameters 'ssh_key_file' and 'password' are mutually exclusive")

    if repo == 'disk':
        mandatoryList += ['image_name']
        unsupportedList = ['file_list', 'host_name', 'user_id', 'password', 'ssh_key_file', 'mount_loc', 'option', 'directory', 'usb_file_loc', 'save']
    elif repo == 'ibmwebsite':
        mandatoryList += ['image_name']
        unsupportedList = ['file_list', 'host_name', 'user_id', 'password', 'ssh_key_file', 'mount_loc', 'option', 'directory', 'usb_file_loc']
    elif repo == 'nfs':
        mandatoryList += ['mount_loc']
        unsupportedList = ['user_id', 'password', 'ssh_key_file', 'usb_file_loc']
    elif repo == 'sftp':
        mandatoryList += ['user_id']
        unsupportedList = ['mount_loc', 'option', 'usb_file_loc']
    elif repo == 'usb':
        mandatoryList += ['usb_file_loc']
        unsupportedList = ['file_list', 'host_name', 'user_id', 'password', 'ssh_key_file', 'mount_loc', 'option', 'directory', 'save']

    logger.debug("mandatory list: %s",mandatoryList)
    logger.debug("Unsupported list: %s",unsupportedList)

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
            raise ParameterError("unsupported parameters: %s" % (','.join(collate)))


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = None
    unsupportedList = []
    mandatoryList = []

    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']

    if opr in ['update', 'upgrade']:
        mandatoryList = ['hmc_host', 'hmc_auth', 'attributes']

    collate = []
    for eachMandatory in mandatoryList:
        if not params[eachMandatory]:
            collate.append(eachMandatory)
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))
    validate_sub_params(params)


def ensure_update(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    vios_name = attributes['vios_name'] or attributes['vios_id']
    m_system = attributes['system']
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['vios_id'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")

    try:
        hmc.removeViosBk(configDict=attributes)
    except HmcError as error:
        if USER_AUTHORITY_ERR in repr(error):
            logger.debug(repr(error))
            return False, None, None
        else:
            raise
    changed = True
    return changed, None, None


def perform_task(module):
    params = module.params
    actions = {
        "update": ensure_update,
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
                      )
                      ),
        state=dict(type='str', choices=['update']),
        attributes=dict(type='dict',
                        required=True,
                        options=dict(
                            repository=dict(required=True, type='str', choices=['disk', 'nfs', 'sftp', 'usb', 'ibmwebsite']),
                            system_name=dict(type='str'),
                            vios_id=dict(type='int'),
                            vios_name=dict(type='str'),
                            image_name=dict(type='str'),
                            file_list=dict(type='list', elements='str'),
                            host_name=dict(type='str'),
                            user_id=dict(type='str'),
                            password=dict(type='str'),
                            ssh_key_file=dict(type='str'),
                            mount_loc=dict(type='str'),
                            directory=dict(type='str'),
                            option=dict(type='str'),
                            usb_file_loc=dict(type='str'),
                            restart=dict(type='bool'),
                            save=dict(type='bool'),
                        )
                        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
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
    result['info'] = info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
