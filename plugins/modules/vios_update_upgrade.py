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

EXAMPLES = '''
- name: Get the current version of VIOS
  vios_update_upgrade :
      hmc_host: '{{ hmc_ip }}'
      hmc_auth: '{{ curr_hmc_auth }}'
      attributes:
        vios_name: <vios_name>
        system_name: <sys>
      state: facts

 - name: Update VIOS using sftp
   vios_update_upgrade:
      hmc_host: '{{ hmc_ip }}'
      hmc_auth: '{{ curr_hmc_auth }}'
      attributes:
        repository: disk
        vios_id: <vios_id>
        system_name: <sys>
        password: <pass>
        user_id: <username>
        host_name: <hostip>
      state: updated

- name: Upgarde VIOS using sftp
   vios_update_upgrade:
      hmc_host: '{{ hmc_ip }}'
      hmc_auth: '{{ curr_hmc_auth }}'
      attributes:
        repository: disk
        vios_id: <vios_id>
        system_name: <sys>
        password: <pass>
        user_id: <username>
        host_name: <hostip>
        disk_list:
         - Disk1
         - Disk2
      state: upgraded

'''

RETURN = '''
Command_output:
    description: Respective user configuration
    type: dict
    returned: on success of all states except C(absent)
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc_vios_update.log"
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
    params = params['attributes']
    mandatoryList = ['repository', 'system_name']
    if opr == 'facts':
        mandatoryList = ['system_name']
    count = sum(x is not None for x in [params['vios_id'], params['vios_name']])
    if count == 0:
        raise ParameterError("Missing VIOS details")
    if count != 1:
        raise ParameterError("Parameters 'vios_id' and 'vios_name' are mutually exclusive")
    
    repo = params['repository']

    if opr == 'updated':
        unsupportedList += ['disk_list']
    elif opr == 'upgraded':
        mandatoryList += ['disk_list']
        unsupportedList += ['restart']

    if opr == 'facts':
        unsupportedList += ['file_list', 'host_name', 'user_id', 'password', 'ssh_key_file', 'repository', 'restart',
                            'mount_loc', 'option', 'directory', 'usb_file_loc', 'save', 'disk_list', 'image_name']

    if repo == 'sftp':
        count = sum(x is not None for x in [params['ssh_key_file'], params['password']])
        if count != 1 and count !=0:
            raise ParameterError("Parameters 'ssh_key_file' and 'password' are mutually exclusive")

    if repo == 'disk':
        mandatoryList += ['image_name']
        unsupportedList += ['file_list', 'host_name', 'user_id', 'password', 'ssh_key_file', 'mount_loc', 'option', 'directory', 'usb_file_loc', 'save']
    elif repo == 'ibmwebsite':
        mandatoryList += ['image_name']
        unsupportedList += ['file_list', 'host_name', 'user_id', 'password', 'ssh_key_file', 'mount_loc', 'option', 'directory', 'usb_file_loc']
    elif repo == 'nfs':
        mandatoryList += ['mount_loc', 'host_name']
        unsupportedList += ['user_id', 'password', 'ssh_key_file', 'usb_file_loc']
    elif repo == 'sftp':
        mandatoryList += ['user_id', 'host_name']
        unsupportedList += ['mount_loc', 'option', 'usb_file_loc']
    elif repo == 'usb':
        mandatoryList += ['usb_file_loc']
        unsupportedList += ['file_list', 'host_name', 'user_id', 'password', 'ssh_key_file', 'mount_loc', 'option', 'directory', 'save']

    collate = []
    for eachUnsupported in unsupportedList:
        if params[eachUnsupported]:
            collate.append(eachUnsupported)

    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (','.join(collate)))
        
    collate = []
    for eachMandatory in mandatoryList:
        if not params[eachMandatory]:
            collate.append(eachMandatory)
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))


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

def facts(module,params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    vios_name = attributes['vios_name'] or attributes['vios_id']
    m_system = attributes['system_name']
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
    if attributes['vios_name'] is not None:
        version = hmc_conn.execute("viosvrcmd -p {0} -m {1} -c ioslevel".format(vios_name,m_system)).strip()
    elif attributes['vios_id'] is not None:
        version = hmc_conn.execute("viosvrcmd --id {0} -m {1} -c ioslevel".format(vios_name,m_system)).strip()
    version=        {
            "vios": vios_name,
            "system": m_system,
            "version": version
        }
    return False, version, None

def ensure_update_upgrade(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    vios_name = attributes['vios_name'] or attributes['vios_id']
    m_system = attributes['system_name']
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
    
    if attributes['repository'] in ['nfs', 'sftp']:
        if attributes['save'] is not None and attributes['image_name'] is None:
            raise ParameterError("To save the image to the HMC hard disk, 'image_name' parameter is required")
        if attributes['save'] is None and attributes['image_name'] is not None:
            raise ParameterError("For remote server repository'image_name' parameter is only required if 'save' option is set to 'true'")

    files=''  
    if attributes['file_list'] is not None:
        for each in attributes['file_list']:
            files += each + ','
    if files[:-1] != '':
        attributes['file_list'] = files[:-1]

    disk=''
    if attributes['disk_list'] is not None:
        for each in attributes['disk_list']:
            disk += each + ','
    if disk[:-1] != '':
        attributes['disk_list'] = disk[:-1]

    try:
        hmc.updatevios(module.params['state'], configDict=attributes)
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
        "updated": ensure_update_upgrade,
        "upgraded": ensure_update_upgrade,
        "facts": facts,
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
        state=dict(type='str', choices=['updated', 'upgraded', 'facts']),
        attributes=dict(type='dict',
                        required=True,
                        options=dict(
                            repository=dict(type='str', choices=['disk', 'nfs', 'sftp', 'usb', 'ibmwebsite']),
                            system_name=dict(type='str'),
                            vios_id=dict(type='str'),
                            vios_name=dict(type='str'),
                            image_name=dict(type='str'),
                            file_list=dict(type='list', elements='str'),
                            host_name=dict(type='str'),
                            user_id=dict(type='str'),
                            password=dict(type='str'),
                            ssh_key_file=dict(type='str'),
                            mount_loc=dict(type='str'),
                            directory=dict(type='str'),
                            option=dict(type='str', choices=['3', '4']),
                            usb_file_loc=dict(type='str'),
                            restart=dict(type='bool'),
                            save=dict(type='bool'),
                            disk_list=dict(type='list', elements='str'),
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
