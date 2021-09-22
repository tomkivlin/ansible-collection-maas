#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: maas_machine_state_info

short_description: Get MaaS machine state

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Gets the state of a machine in MaaS from the system_id or hostname

options:
    hostname:
        description: Hostname of the machine.
        required: false
        type: str
    system_id:
        description: The system_id of the machine.
        required: false
        type: str
    maas_url:
        description: The URL of the MaaS server. Can use MAAS_URL environment variable instead.
        required: false
        type: str
    maas_apikey:
        description: The API Key for authentication to the MaaS server. Can use MAAS_APIKEY environment variable instead.
        required: false
        type: str
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - gtlabs.maas.maas_machine_state_info

author:
    - Tom Kivlin (@tomkivlin)
'''

EXAMPLES = r'''
# Get information based on the hostname
- name: Get information based on the hostname
  tomkivlin.maas.maas_machine_state_info:
    hostname: server1
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf

# Get information based on the system_id
- name: Get information based on the system_id
  tomkivlin.maas.maas_machine_state_info:
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
'''

RETURN = r'''
status:
    description: The status of the machine
    returned: success
    type: str
    sample:
        - COMMISSIONING
        - NEW
        - READY
        - DEPLOYED
'''
import os
import traceback

LIBMAAS_IMP_ERR = None
try:
    from maas.client import connect
    from maas.client.bones import CallError
    HAS_LIBMAAS = True
except ImportError:
    LIBMAAS_IMP_ERR = traceback.format_exc()
    HAS_LIBMAAS = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def status_map(maas_status_id):
    if maas_status_id == 0:
        maas_status = 'NEW'
    elif maas_status_id == 1:
        maas_status = 'COMMISSIONING'
    elif maas_status_id == 2:
        maas_status = 'FAILED_COMMISSIONING'
    elif maas_status_id == 3:
        maas_status = 'MISSING'
    elif maas_status_id == 4:
        maas_status = 'READY'
    elif maas_status_id == 5:
        maas_status = 'RESERVED'
    elif maas_status_id == 6:
        maas_status = 'DEPLOYED'
    elif maas_status_id == 7:
        maas_status = 'RETIRED'
    elif maas_status_id == 8:
        maas_status = 'BROKEN'
    elif maas_status_id == 9:
        maas_status = 'DEPLOYING'
    elif maas_status_id == 10:
        maas_status = 'ALLOCATED'
    elif maas_status_id == 11:
        maas_status = 'FAILED_DEPLOYMENT'
    elif maas_status_id == 12:
        maas_status = 'RELEASING'
    elif maas_status_id == 13:
        maas_status = 'FAILED_RELEASING'
    elif maas_status_id == 14:
        maas_status = 'DISK_ERASING'
    elif maas_status_id == 15:
        maas_status = 'FAILED_DISK_ERASING'
    elif maas_status_id == 16:
        maas_status = 'RESCUE_MODE'
    elif maas_status_id == 17:
        maas_status = 'ENTERING_RESCUE_MODE'
    elif maas_status_id == 18:
        maas_status = 'FAILED_ENTERING_RESCUE_MODE'
    elif maas_status_id == 19:
        maas_status = 'EXITING_RESCUE_MODE'
    elif maas_status_id == 20:
        maas_status = 'FAILED_EXITING_RESCUE_MODE'
    elif maas_status_id == 21:
        maas_status = 'TESTING'
    elif maas_status_id == 22:
        maas_status = 'FAILED_TESTING'
    else:
        maas_status = 'UNKNOWN'

    return maas_status


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        hostname=dict(type='str', required=False),
        system_id=dict(type='str', required=False),
        maas_url=dict(type='str', required=False),
        maas_apikey=dict(type='str', required=False, no_log=True)
    )

    result = {"changed": False}

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_LIBMAAS:
        module.fail_json(msg=missing_required_lib('python-libmaas'), exception=LIBMAAS_IMP_ERR)

    hostname = module.params['hostname']
    system_id = module.params['system_id']
    maas_url = (
        module.params['maas_url']
        or os.getenv("MAAS_URL")
    )
    maas_apikey = (
        module.params['maas_apikey']
        or os.getenv("MAAS_APIKEY")
    )

    if hostname or system_id:

        try:
            maas = connect(maas_url, apikey=maas_apikey)
        except CallError:
            module.fail_json(msg='Unable to connect - please check the URL!', **result)

        if system_id:
            try:
                maas_machine = maas.machines.get(system_id=system_id)
                maas_status_id = maas_machine.status
                maas_status = status_map(maas_status_id)
            except CallError:
                module.fail_json(msg='No machine matching system ID %s in MaaS or API key not authorised!' % system_id, **result)
        elif hostname:
            try:
                maas_machine = maas.machines.list(hostnames=[hostname])
                maas_system_id = maas_machine[0].system_id
                maas_machine = maas.machines.get(system_id=maas_system_id)
                maas_status_id = maas_machine.status
                maas_status = status_map(maas_status_id)
            except (CallError, IndexError):
                module.fail_json(msg='No machine matching hostname %s in MaaS or API key not authorised!' % hostname, **result)
        else:
            module.fail_json(msg='One of system_id or hostname is required.', **result)

        if module.check_mode:
            module.exit_json(**result)

        result = {"changed": False, "status": maas_status, "status_id": maas_status_id}

        module.exit_json(**result)

    else:
        module.fail_json(msg='One of system_id or hostname is required.', **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
