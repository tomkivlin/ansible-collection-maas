#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: maas_machine_state

short_description: Manage MaaS machine state

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Manages the state of a machine in MaaS from a given device ID

options:
    hostname:
        description: Hostname to be configured.
        required: no
        type: str
    system_id:
        description: The system_id of the machine to be configured.
        required: no
        type: str
    maas_url:
        description: The URL of the MaaS server. Can use MAAS_URL environment variable instead.
        type: str
    maas_apikey:
        description: The API Key for authentication to the MaaS server. Can use MAAS_APIKEY environment variable instead.
        type: str
    status:
        description:
        - The desired state of the machine.
        - If 'commissioned' then the machine will be commissioned and all configuration wiped before being powered off.
        - If 'released' then the machine will be released and powered off.
        - If 'deployed' then the machine will have an OS deployed.
        required: yes
        type: str
    force:
        description:
        - If 'no' then the task will fail if the machine is not in the correct state (e.g. cannot deploy unless the machine is in the READY state)
        - If 'yes' then the machine will be forced to that state (e.g. if the machine is already deployed, it will first be released to the READY state)
        type: bool
        default: no
    distro_series:
        description:
        - The OS/distro to deploy to the machine.
        - If not supplied, the default OS/distro will be deployed.
        type: str
    user_data:
        description:
        - The user_data to deploy to the machine.
        - If not supplied, the default OS/distro will be deployed.
        type: str
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - tomkivlin.maas.maas_machine_state

author:
    - Tom Kivlin (@tomkivlin)
'''

EXAMPLES = r'''
# Commission the machine
- name: Commission the machine
  tomkivlin.maas.maas_machine_state:
    hostname: server1
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: commissioned

# Commission the machine with extra scripts
- name: Commission the machine
  tomkivlin.maas.maas_machine_state:
    hostname: server1
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: commissioned
    scripts:
      - clear_hardware_raid

# Release the machine
- name: Release the machine
  tomkivlin.maas.maas_machine_state:
    hostname: server1
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: released

# Deploy the machine using default OS/distro
- name: Deploy the machine
  tomkivlin.maas.maas_machine_state:
    hostname: server1
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: deployed

# Deploy the machine using specified OS/distro, using environment variables for the URL and API key
- name: Deploy ESXi to the machine
  tomkivlin.maas.maas_machine_state:
    hostname: server1
    system_id: y3b3x3
    status: deployed
    os: esxi/7.0u1c

# Force-deploy the machine using specified OS/distro, using environment variables for the URL and API key
- name: Deploy ESXi to the machine
  tomkivlin.maas.maas_machine_state:
    hostname: server1
    system_id: y3b3x3
    status: deployed
    os: esxi
    distro: 7.0u1c
    force: yes
'''

RETURN = r'''
# Default return values
'''
import os
import traceback

LIBMAAS_IMP_ERR = None
try:
    from maas.client import connect
    from maas.client.bones import CallError
    from maas.client.enum import NodeStatus
    HAS_LIBMAAS = True
except ImportError:
    LIBMAAS_IMP_ERR = traceback.format_exc()
    HAS_LIBMAAS = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        hostname=dict(type='str', required=False),
        system_id=dict(type='str', required=False),
        maas_url=dict(type='str', required=False),
        maas_apikey=dict(type='str', required=False),
        status=dict(type='str', required=True),
        force=dict(type='bool', required=False, default=False),
        distro_series=dict(type='str', required=False),
        user_data=dict(type='str', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

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
    domain = module.params['domain']
    system_id = module.params['system_id']
    maas_url = (
        module.params['maas_url']
        or os.getenv("MAAS_URL")
    )
    maas_apikey = (
        module.params['maas_apikey']
        or os.getenv("MAAS_APIKEY")
    )
    status = module.params['status']
    force = module.params['force']
    distro_series = module.params['distro_series']
    user_data = module.params['user_data']

    if hostname or system_id:

        try:
            maas = connect(maas_url, apikey=maas_apikey)
        except CallError:
            module.fail_json(
                msg='Unable to connect - please check the URL!', **result)

        if system_id:
            try:
                maas_machine = maas.machines.get(system_id=system_id)
            except CallError:
                module.fail_json(
                    msg='No machine matching system ID %s in MaaS or API key not authorised!' % system_id, **result)
        elif hostname:
            try:
                maas_machine = maas.machines.list(hostnames=hostname)
                maas_system_id = maas_machine[0].system_id
                maas_machine = maas.machines.get(system_id=maas_system_id)
            except (CallError, IndexError):
                module.fail_json(
                    msg='No machine matching hostname %s in MaaS or API key not authorised!' % hostname, **result)
        else:
            module.fail_json(msg='One of system_id or hostname is required.', **result)

        # Get the machine status.
        # Run through the various permutations.
        maas_status = maas_machine.status
        if status == 'commissioned':
            try:
                if maas_status == NodeStatus.NEW:
                    # This is OK - commission the machine
                    try:
                        maas_machine.commission(wait=False)
                        result['changed'] = True
                    except (CallError):
                        module.fail_json(msg='Commission is not available because the machine is not in the correct state.', **result)
                if maas_status == (NodeStatus.READY or NodeStatus.ALLOCATED or NodeStatus.BROKEN):
                    # This means the machine has already been commissioned, only do it if force = yes
                    if force:
                        # Set the machine to commission and don't wait
                        maas_machine.commission(wait=False)
                        result['changed'] = True
                    else:  # force = no
                        result['changed'] = False
            except (CallError):
                module.fail_json(msg='Commission is not available because the machine is not in the correct state.', **result)
        if status == 'released':
            # This action, which includes the 'Power off' action,
            # releases a node back into the pool of available nodes,
            # changing a node's status from 'Deployed' (or 'Allocated') to 'Ready'.
            try:
                if maas_status == (NodeStatus.ALLOCATED or NodeStatus.DEPLOYED or NodeStatus.DEPLOYING):
                    # This is an ok state to release the node from
                    maas_machine.release()
                    result['changed'] = True
                elif maas_status == NodeStatus.READY:
                    result['changed'] = False
            except (CallError):
                module.fail_json(msg='Machine cannot be released in its current state.', **result)
        if status == 'deployed':
            if maas_status == (NodeStatus.READY or NodeStatus.ALLOCATED):
                # This is OK to do without force = yes
                if (user_data is not None) and (distro_series is not None):
                    try:
                        maas_machine.deploy(user_data=user_data, distro_series=distro_series)
                        result['changed'] = True
                    except (CallError):
                        module.fail_json(msg='Deploy failed - check the machine config, e.g. storage is mounted correctly.', **result)
                elif distro_series and (user_data is None):
                    try:
                        maas_machine.deploy(distro_series=distro_series)
                        result['changed'] = True
                    except (CallError):
                        module.fail_json(msg='Deploy failed - check the machine config, e.g. storage is mounted correctly.', **result)
                elif user_data and (distro_series is None):
                    try:
                        maas_machine.deploy(user_data=user_data)
                        result['changed'] = True
                    except (CallError):
                        module.fail_json(msg='Deploy failed - check the machine config, e.g. storage is mounted correctly.', **result)
                else:
                    try:
                        maas_machine.deploy()
                        result['changed'] = True
                    except (CallError):
                        module.fail_json(msg='Deploy failed - check the machine config, e.g. storage is mounted correctly.', **result)
            else:
                # Any other state - need to release first but only if force = yes
                if force:
                    # Release the machine and deploy
                    maas_machine.release()
                    maas_machine.deploy()
                    result['changed'] = True
                else:  # force = no
                    result['changed'] = False
            # except (CallError):
            #     module.fail_json(msg='Cannot deploy a machine that is in the Deployed or Broken state. Use force = yes to force this.', **result)

        if module.check_mode:
            module.exit_json(**result)

        result = {"changed": False, "data": maas_machine._data}

        module.exit_json(**result)

    else:
        module.fail_json(msg='One of system_id or hostname is required.', **result)

    if module.check_mode:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
