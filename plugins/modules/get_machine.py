#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: get_machine

short_description: Get info about a MaaS machine

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.2.0"

description: Gets all info about a machine in MaaS from the system_id or hostname

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
#     - gtlabs.maas.my_doc_fragment_name

author:
    - Tom Kivlin (@tom-kivlin)
'''

EXAMPLES = r'''
# Get information based on the hostname
- name: Get information based on the hostname
  gtlabs.maas.get_machine:
    hostname: server1
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf

# Get information based on the system_id
- name: Get information based on the system_id
  gtlabs.maas.get_machine:
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
'''

RETURN = r'''
# Cut-down output
ok: [localhost] => {
    "result": {
        "changed": false,
        "data": {
            "address_ttl": null,
            "architecture": "amd64/generic",
            "bcaches": [],
            "bios_boot_method": "uefi",
            "blockdevice_set": [
                {
                    ...
                }
            ],
            "boot_disk": {
                ...
            },
            "boot_interface": {
                ...
            },
            "cache_sets": [],
            "commissioning_status": 2,
            "commissioning_status_name": "Passed",
            "cpu_count": 48,
            "cpu_speed": 2300,
            "cpu_test_status": -1,
            "cpu_test_status_name": "Unknown",
            "current_commissioning_result_id": 684,
            "current_installation_result_id": null,
            "current_testing_result_id": 687,
            "default_gateways": {
                ...
            },
            "description": "",
            "disable_ipv4": false,
            "distro_series": "",
            "domain": {
                ...
            },
            "fqdn": "server1.maas",
            "hardware_info": {
                ...
            },
            "hardware_uuid": "37383638-3530-5A43-3238-323130354A47",
            "hostname": "server1",
            "hwe_kernel": null,
            "interface_set": [
                {
                    ...
                }
            ],
            "interface_test_status": -1,
            "interface_test_status_name": "Unknown",
            "ip_addresses": [],
            "iscsiblockdevice_set": [],
            "locked": false,
            "memory": 67584,
            "memory_test_status": -1,
            "memory_test_status_name": "Unknown",
            "min_hwe_kernel": "",
            "netboot": true,
            "network_test_status": -1,
            "network_test_status_name": "Unknown",
            "node_type": 0,
            "node_type_name": "Machine",
            "numanode_set": [
                {
                    ...
                }
            ],
            "osystem": "",
            "other_test_status": -1,
            "other_test_status_name": "Unknown",
            "owner": null,
            "owner_data": {},
            "physicalblockdevice_set": [
                {
                    ...
                }
            ],
            "pod": null,
            "pool": {
                ...
            },
            "power_state": "off",
            "power_type": "ipmi",
            "raids": [],
            "resource_uri": "/MAAS/api/2.0/machines/y3b3x3/",
            "special_filesystems": [],
            "status": 4,
            "status_action": "",
            "status_message": "Loading ephemeral",
            "status_name": "Ready",
            "storage": 17843526.844416,
            "storage_test_status": 2,
            "storage_test_status_name": "Passed",
            "swap_size": null,
            "system_id": "y3b3x3",
            "tag_names": [],
            "testing_status": 2,
            "testing_status_name": "Passed",
            "virtualblockdevice_set": [],
            "virtualmachine_id": null,
            "volume_groups": [],
            "zone": {
                ...
            }
        },
        "failed": false
'''
import os
import traceback

LIBMAAS_IMP_ERR = None
try:
    from maas.client import connect
    HAS_LIBMAAS = True
except ImportError:
    LIBMAAS_IMP_ERR = traceback.format_exc()
    HAS_LIBMAAS = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from maas.client.bones import CallError


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        hostname=dict(type='str', required=False),
        system_id=dict(type='str', required=False),
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
                maas_machine_power = maas.machines.get_power_parameters_for(system_ids=[system_id])
            except CallError:
                module.fail_json(msg='No machine matching system ID %s in MaaS or API key not authorised!' % system_id, **result)
        elif hostname:
            try:
                maas_machine = maas.machines.list(hostnames=hostname)
                maas_system_id = maas_machine[0].system_id
                maas_machine = maas.machines.get(system_id=maas_system_id)
            except (CallError, IndexError):
                module.fail_json(msg='No machine matching hostname %s in MaaS or API key not authorised!' % hostname, **result)
        else:
            module.fail_json(msg='One of system_id or hostname is required.', **result)

        if module.check_mode:
            module.exit_json(**result)

        result = {"changed": False, "data": maas_machine._data, "power_data": maas_machine_power}

        module.exit_json(**result)

    else:
        module.fail_json(msg='One of system_id or hostname is required.', **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
