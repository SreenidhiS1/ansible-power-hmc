RETURN = '''
Command_output:
    description: Respective user configuration
    type: dict
    returned: on success of all states except C(absent)
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc_vios.log"
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

    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']

    if opr in ['present', 'restore']:
        params = params['attributes']
        mandatoryList = ['types', 'system', 'backup_name']
        unsupportedList = ['restart','new_name']
    if opr == 'restore':
        params = params['attributes']
        mandatoryList = ['types', 'system', 'backup_name']
        unsupportedList = ['restart', 'nimol_resource', 'media_repository', 'volume_group_structure', 'file_list','new_name']
    if opr == 'absent':
        params = params['attributes']
        mandatoryList = ['types', 'system', 'file_list']
        unsupportedList = ['restart', 'nimol_resource', 'media_repository', 'volume_group_structure', 'backup_name','new_name']
    if opr == 'modify':
        params = params['attributes']
        mandatoryList = ['types', 'system', 'file_list']
        unsupportedList = ['restart', 'nimol_resource', 'media_repository', 'volume_group_structure', 'file_list']

    if opr in ['present', 'restore', 'absent','modify']:
        count = sum(x is not None for x in [params['id'], params['uuid'], params['vios_name']])
        if count == 0:
           raise ParameterError("Missing parameter for vios details is missing")
        if count!= 1:
            raise ParameterError("Parameters 'id', 'uuid' and 'vios_name' are mutually exclusive")
    if opr == 'present':
        if params['nimol_resource'] != None or params['media_repository'] != None or params['volume_group_structure'] != None:
                if params['types'] != 'vios':
                    raise ParameterError("Parameters 'nimol_resource', 'media_repository' and 'volume_group_structure' are valid for only full VIOS backup")
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

    if opr in ['present', 'restore']:
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

    collate = []
    for eachUnsupported in unsupportedList:
        if params[eachUnsupported]:
            collate.append(eachUnsupported)

    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (','.join(collate)))
    validate_sub_params(params)


def facts(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}
    viosbk_details = []
    
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        viosbk_details = hmc.listViosbk(filt=filter_d)
    except HmcError as error:
        if USER_AUTHORITY_ERR in repr(error):
            logger.debug(repr(error))
            return False, None, None
        else:
            raise
    return False, viosbk_details, None

def ensure_present(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    
    vios_name = attributes['vios_name'] or attributes['id'] or attributes['uuid']
    m_system = attributes['system']
    sys_list = (
    hmc_conn.execute("lssyscfg -r sys -F name").splitlines() +
    hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['id'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['uuid'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] != None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['id'] != None:
                filter_d = {"VIOS_IDS": attributes['id'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['uuid'] != None:
                filter_d = {"VIOS_UUIDS": attributes['uuid'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}            
            vios_list = hmc.listViosbk(filter_d)
            vios_list = [item['NAME'].split('.')[0] for item in vios_list]
            if attributes['backup_name'] in vios_list:
                msg = "The backup file {0} already exists".format(attributes['backup_name'])
                return False,None,msg
            else:
                try: 
                    hmc.createViosBk(configDict=attributes)
                    if attributes['vios_name'] != None:
                        filter_d = {"VIOS_NAMES": attributes['vios_name'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
                    elif attributes['id'] != None:
                        filter_d = {"VIOS_IDS": attributes['id'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
                    elif attributes['uuid'] != None:
                        filter_d = {"VIOS_UUIDS": attributes['uuid'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
                    viosbk_info = hmc.listViosbk(filter_d)
                except HmcError as error:
                    if USER_AUTHORITY_ERR in repr(error):
                        logger.debug(repr(error))
                        return False, None, None
                    else:
                        raise          
                changed = True
                return changed, viosbk_info, None
        
def ensure_restore(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    
    m_system = attributes['system']
    vios_name = attributes['vios_name'] or attributes['id'] or attributes['uuid']
    if attributes['types'] not in ['viosioconfig', 'ssp']:
        module.warn(msg="For restore the type can be either viosioconfig or ssp")
    m_system = attributes['system']
    sys_list = (
    hmc_conn.execute("lssyscfg -r sys -F name").splitlines() +
    hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC") 
    else:
        if attributes['vios_name'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['id'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['uuid'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] != None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['id'] != None:
                filter_d = {"VIOS_IDS": attributes['id'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['uuid'] != None:
                filter_d = {"VIOS_UUIDS": attributes['uuid'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}            
            vios_list = hmc.listViosbk(filter_d)
            vios_list = [item['NAME'] for item in vios_list]
            if attributes['backup_name'] not in vios_list:
                msg = "The backup file {0} does not exists".format(attributes['backup_name'])
                return False,None,msg
            else:
                try:
                    hmc.restoreViosBk(configDict=attributes)
                except HmcError as error:
                    if USER_AUTHORITY_ERR in repr(error):
                        logger.debug(repr(error))
                        return False, None, None
                    else:
                        raise
                changed = True
                return changed, None, None
            
def ensure_absent(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    
    vios_name = attributes['vios_name'] or attributes['id'] or attributes['uuid']
    m_system = attributes['system']
    sys_list = (
    hmc_conn.execute("lssyscfg -r sys -F name").splitlines() +
    hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['id'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['uuid'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] != None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['id'] != None:
                filter_d = {"VIOS_IDS": attributes['id'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['uuid'] != None:
                filter_d = {"VIOS_UUIDS": attributes['uuid'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}            
            backup_list = hmc.listViosbk(filter_d)
            backup_list = [item['NAME'] for item in backup_list]
            file_list = attributes['file_list']
            removed_list = []
            for each in file_list[:]:
                if each not in backup_list:
                    removed_list.append(each)
                    file_list.remove(each)
            if len(file_list) != 0:
                attributes['backup_name'] = ','.join(map(str, file_list))
            else:
                msg = "Specified backup files are not available"
                return None, None, msg
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

def ensure_modify(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    
    vios_name = attributes['vios_name'] or attributes['id'] or attributes['uuid']
    m_system = attributes['system']
    sys_list = (
    hmc_conn.execute("lssyscfg -r sys -F name").splitlines() +
    hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['id'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['uuid'] != None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] != None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['id'] != None:
                filter_d = {"VIOS_IDS": attributes['id'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}
            elif attributes['uuid'] != None:
                filter_d = {"VIOS_UUIDS": attributes['uuid'],"SYS_NAMES": attributes['system'],"TYPES": attributes['types']}            
            backup_list = hmc.listViosbk(filter_d)
            if attributes['backup_name'] not in backup_list:
                msg = "Specified backup files are not available"
                return None, None, msg
            else:
                try:
                    hmc.modifyViosBk(configDict=attributes)
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
        "facts": facts,
        "present": ensure_present,
        "restore": ensure_restore,
        "absent": ensure_absent,
        "modify": ensure_modify,
    }

    if not params['hmc_auth']:
        return False, "missing credential info", None

    oper = 'state'
    if params['state'] is None:
        oper = 'action'

    try:
        return actions[params[oper]](module, params)
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
        state=dict(type='str',choices=['facts','present', 'restore', 'absent','modify']),
        attributes=dict(type='dict',
                        options=dict(
                            types=dict(type='str',choices=['viosioconfig', 'vios', 'ssp']),
                            system=dict(type='str'),
                            id=dict(type='str'),
                            uuid=dict(type='str'),
                            vios_name=dict(type='str'),
                            backup_name=dict(tye='str'),
                            file_list=dict(type='list'),
                            nimol_resource=dict(type='int', choices=[0,1]),
                            media_repository=dict(type='int', choices=[0,1]),
                            volume_group_structure=dict(type='int', choices=[0,1]),
                            restart=dict(type='bool'),
                            new_name=dict(type='str')
                        )
                        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
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
