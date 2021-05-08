#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from aiohttp.client_exceptions import ClientConnectorError
from maas.client.bones import CallError
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
import json
import warnings
import traceback
import os

__metaclass__ = type

DOCUMENTATION = r'''
---
module: get_system_id

short_description: Get system_id of MaaS machine

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.2.2"

description: Gets system_id from hostname or power_address

options:
    hostname:
        description: The hostname of the machine. If not included, power_address must be used.
        required: false
        type: str
    power_address:
        description: The power_address of the machine (e.g. BMC, iLo, iDRAC). If not included, hostname must be used.
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
#     - gtlabs.maas.my_doc_fragment_name

author:
    - Tom Kivlin (@tom-kivlin)
'''

EXAMPLES = r'''
# Get information based on the hostname
- name: Get information about machine based on hostname
  gtlabs.maas.get_system_id:
    hostname: server1
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf

# Get information based on the system_id
- name: Get information based on the system_id
  gtlabs.maas.get_system_id:
    power_address: 10.1.1.100
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
'''

RETURN = r'''
ok: [localhost] => {
    "result": {
        "changed": false,
        "failed": false,
        "system_id": "7pxm3s"
    }
}
'''

LIBMAAS_IMP_ERR = None
try:
    from maas.client import connect
    HAS_LIBMAAS = True
except ImportError:
    LIBMAAS_IMP_ERR = traceback.format_exc()
    HAS_LIBMAAS = False


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        hostname=dict(type='str', required=False),
        power_address=dict(type='str', required=False),
        maas_url=dict(type='str', required=False),
        maas_apikey=dict(type='str', required=False)
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
        module.fail_json(msg=missing_required_lib(
            'python-libmaas'), exception=LIBMAAS_IMP_ERR)

    hostname = module.params['hostname']
    power_address = module.params['power_address']
    maas_url = (
        module.params['maas_url']
        or os.getenv("MAAS_URL")
    )
    maas_apikey = (
        module.params['maas_apikey']
        or os.getenv("MAAS_APIKEY")
    )
    maas_system_id = ''

    if hostname or power_address:

        try:
            maas = connect(maas_url, apikey=maas_apikey)
        except CallError:
            module.fail_json(
                msg='Unable to connect - please check the URL and API key!', **result)

        if hostname:
            try:
                maas_machine = maas.machines.list(hostnames=hostname)
                maas_system_id = maas_machine[0].system_id
            except (CallError, IndexError):
                module.fail_json(
                    msg='No machine matching hostname %s in MaaS or API key not authorised!' % hostname, **result)
        elif power_address:
            all_maas_machines = maas.machines.list()
            output = print(all_maas_machines)
            for maas_machine in all_maas_machines:
                maas_power = maas_machine.get_power_parameters()
                for key, value in maas_power.items():
                    if "power_address" in key:
                        maas_power_address = value
                        if maas_power_address == power_address:
                            maas_system_id = maas_machine.system_id

        else:
            module.fail_json(
                msg='One of power_address or hostname is required.', **result)

        if module.check_mode:
            module.exit_json(**result)

        result = {"changed": False, "system_id": maas_system_id}

        module.exit_json(**result)

    else:
        module.fail_json(
            msg='One of power_address or hostname is required.', **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
