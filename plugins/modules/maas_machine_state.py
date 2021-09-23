#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from requests_oauthlib import OAuth1
from requests import Request, Session
import time
import traceback
import os

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
    system_id:
        description: The system_id of the machine to be configured.
        required: yes
        type: str
    maas_url:
        description: The URL of the MaaS server. Can use MAAS_URL environment variable instead.
        type: str
    maas_apikey:
        description: The API Key for authentication to the MaaS server. Can use MAAS_APIKEY environment variable instead.
        type: str
    state:
        description:
        - The desired state of the machine.
        - If 'commissioned' then the machine will be commissioned and all configuration wiped before being powered off.
        - If 'ready' then the machine will be released and powered off.
        - If 'deployed' then the machine will have an OS deployed.
        required: yes
        type: str
        choices: ['commissioned', 'ready', 'deployed']
    scripts:
        description: The commissioning scripts to use - ignored unless state = commissioned
        required: no
        type: list
        elements: str
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
    b64_user_data:
        description:
        - The user_data to deploy to the machine.
        - This must already be encoded in base64.
        type: str
    boot_disk:
        description:
        - The physical disk to use as the boot disk
        - This can be the name (e.g. sda) or serial (e.g. 5000c5009577d02b)
        type: str
    storage_layout:
        description: The storage layout to apply; select from 'flat', 'lvm' or 'blank'
        type: str
        choices: ['blank', 'lvm', 'flat', 'vmfs6']
    vlans:
        description: The vlans that need to be applied to the machine configuration.
        type: list
        elements: dict
        suboptions:
            vlan_id:
                description: The VLAN ID to use - don't use quotes, this needs to be an integer.
                type: int
            parent:
                description: The name of the parent interface to which this VLAN interface is attached.
                type: str
            subnet_cidr:
                description: The CIDR of the subnet associated with this VLAN.
                type: str
            link_mode:
                description: Choice of DHCP, AUTO, or STATIC.
                type: str
                choices: ['static', 'auto', 'dhcp']
            ip_address:
                description: The IP address of the interface.
                type: str
            state:
                description: The state of the interface, choose from present or absent.
                type: str
                choices: ['present', 'absent']
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
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: commissioned

# Commission the machine with extra scripts
- name: Commission the machine
  tomkivlin.maas.maas_machine_state:
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: commissioned
    scripts:
      - clear_hardware_raid

# Release the machine
- name: Release the machine
  tomkivlin.maas.maas_machine_state:
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: ready

# Deploy the machine using default OS/distro
- name: Deploy the machine
  tomkivlin.maas.maas_machine_state:
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
    status: deployed

# Deploy the machine using specified OS/distro, using environment variables for the URL and API key
- name: Deploy ESXi to the machine
  tomkivlin.maas.maas_machine_state:
    system_id: y3b3x3
    status: deployed
    distro_series: 7.0u1c

# Force-deploy the machine using specified OS/distro, using environment variables for the URL and API key
- name: Deploy ESXi to the machine
  tomkivlin.maas.maas_machine_state:
    system_id: y3b3x3
    status: deployed
    distro_series: 7.0u1c
    force: yes
'''

RETURN = r'''
# Default return values
'''

LIBMAAS_IMP_ERR = None
try:
    from maas.client import connect
    from maas.client.bones import CallError
    from maas.client.enum import NodeStatus
    from maas.client.enum import BlockDeviceType
    from maas.client.enum import InterfaceType
    from maas.client.enum import LinkMode
    HAS_LIBMAAS = True
except ImportError:
    LIBMAAS_IMP_ERR = traceback.format_exc()
    HAS_LIBMAAS = False


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


def clear_storage(machine):
    clear_storage_result = ''
    for vol_group in machine.volume_groups:
        vol_group.delete()
        clear_storage_result = 'cleared'

    for disk in machine.block_devices:
        if disk.type == BlockDeviceType.VIRTUAL:
            disk.delete()
            clear_storage_result = 'cleared'

    for disk in machine.block_devices:
        if disk.type == BlockDeviceType.PHYSICAL:
            for partition in disk.partitions:
                partition.delete()
                clear_storage_result = 'cleared'
    return clear_storage_result


def set_boot_disk(machine, boot_disk):
    set_boot_disk_result = ''
    for disk in machine.block_devices:
        if disk.type == BlockDeviceType.PHYSICAL:
            if disk.name in boot_disk:
                disk.set_as_boot_disk()
                set_boot_disk_result = 'pass'
            elif disk.serial in boot_disk:
                disk.set_as_boot_disk()
                set_boot_disk_result = 'pass'
            else:
                set_boot_disk_result = 'fail'
    return set_boot_disk_result


def set_storage_layout(system_id, url, apikey, layout):
    set_storage_result = ''
    consumer_key = apikey.split(':')[0]
    token_key = apikey.split(':')[1]
    token_secret = apikey.split(':')[2]
    auth1 = OAuth1(consumer_key, '', token_key, token_secret)
    headers = {'Accept': 'application/json'}
    req_url = url + 'api/2.0/machines/' + system_id + '/?op=set_storage_layout'
    body = dict(storage_layout=layout)
    s = Session()
    req = Request('POST', req_url, data=body, headers=headers, auth=auth1)
    prepped = req.prepare()
    resp = s.send(prepped)
    if resp.status_code == 200:
        set_storage_result = 'success'
    else:
        set_storage_result = 'fail'
    return set_storage_result


def delete_interfaces(machine):
    # This script is not idempotent - first delete any BOND, BRIDGE and VLAN interfaces
    existing_maas_interfaces = machine.interfaces
    for existing_maas_interface in existing_maas_interfaces:
        if existing_maas_interface.type in (InterfaceType.VLAN, InterfaceType.BOND, InterfaceType.BRIDGE):
            existing_maas_interface.delete()
        if existing_maas_interface.type is InterfaceType.PHYSICAL:
            existing_maas_interface.disconnect()


def create_vlan_interface(machine, vlan, client):
    for key, value in vlan.items():
        if 'vlan_id' in key:
            vlan_id = value
        if 'parent' in key:
            parent = value
        if 'subnet_cidr' in key:
            subnet_cidr = value
        if 'link_mode' in key:
            link_mode = value
        if 'ip_address' in key:
            ip_address = value
    maas_subnet = client.subnets.get(subnet_cidr)
    if vlan_id == maas_subnet.vlan.vid:
        vlan_parent = machine.interfaces.get_by_name(name=parent)
        # With the next two lines, the first operation gets the physical interface on the right fabric but also configures the subnet (which we don't want)
        # The second operation resets the link, but doesn't remove the fabric assignment
        vlan_parent.links.create(
            LinkMode.LINK_UP, force=True, subnet=maas_subnet)
        vlan_parent.links.create(LinkMode.LINK_UP, force=True)
        vlan_interface = machine.interfaces.create(
            InterfaceType.VLAN, parent=vlan_parent, vlan=maas_subnet.vlan)
        if 'dhcp' in link_mode:
            vlan_interface.links.create(LinkMode.DHCP, subnet=maas_subnet.id)
        if 'auto' in link_mode:
            vlan_interface.links.create(LinkMode.AUTO, subnet=maas_subnet.id)
        if 'static' in link_mode:
            vlan_interface.links.create(
                LinkMode.STATIC, subnet=maas_subnet.id, ip_address=ip_address)


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        system_id=dict(type='str', required=True),
        maas_url=dict(type='str'),
        maas_apikey=dict(type='str', no_log=True),
        state=dict(type='str', required=True, choices=[
                   'commissioned', 'ready', 'deployed']),
        scripts=dict(type='list', elements='str'),
        force=dict(type='bool', default=False),
        distro_series=dict(type='str'),
        b64_user_data=dict(type='str'),
        boot_disk=dict(type='str'),
        storage_layout=dict(type='str', choices=[
                            'blank', 'flat', 'lvm', 'vmfs6']),
        vlans=dict(type='list', elements='dict', options=dict(
            vlan_id=dict(type='int'),
            parent=dict(type='str'),
            subnet_cidr=dict(type='str'),
            link_mode=dict(type='str', choices=['static', 'auto', 'dhcp']),
            ip_address=dict(type='str'),
            state=dict(type='str', choices=['absent', 'present'])
        ))
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        system_id=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[       # if state = deployed then we need the storage_layout and vlans
            ('state', 'deployed', ('storage_layout', 'vlans'))
        ],
        # if distro_series is specified, we also need storage_layout
        required_by={'distro_series': 'storage_layout'},
        supports_check_mode=True
    )

    if not HAS_LIBMAAS:
        module.fail_json(msg=missing_required_lib(
            'python-libmaas'), exception=LIBMAAS_IMP_ERR)

    system_id = module.params['system_id']
    maas_url = (
        module.params['maas_url']
        or os.getenv("MAAS_URL")
    )
    maas_apikey = (
        module.params['maas_apikey']
        or os.getenv("MAAS_APIKEY")
    )
    state = module.params['state']
    scripts = module.params['scripts']
    force = module.params['force']
    distro_series = module.params['distro_series']
    user_data = module.params['b64_user_data']
    boot_disk = module.params['boot_disk']
    storage_layout = module.params['storage_layout']
    vlans = module.params['vlans']
    if vlans:
        for vlan in vlans:      # Validation that ip_address is provided if link_mode=static.
            if 'static' in vlan['link_mode']:
                if vlan['ip_address'] is None:
                    module.fail_json(
                        msg='vlans.ip_address must be provided if vlans.link_mode: static', **result)
    changed = False

    try:
        maas = connect(maas_url, apikey=maas_apikey)
    except CallError:
        module.fail_json(
            msg='Unable to connect - please check the URL!', **result)

    try:
        maas_machine = maas.machines.get(system_id=system_id)
    except CallError:
        module.fail_json(
            msg='No machine matching system ID %s in MaaS or API key not authorised!' % system_id, **result)

    # Get the machine status.
    # Run through the various permutations.
    maas_status_id = maas_machine.status
    maas_status = status_map(maas_status_id)
    if state == 'commissioned':
        if maas_status_id == NodeStatus.NEW:
            # This is OK - commission the machine
            if scripts:
                maas_machine.commission(
                    wait=False, commissioning_scripts=scripts)
                changed = True
            else:
                maas_machine.commission(wait=False)
                changed = True
        elif maas_status_id in (NodeStatus.READY, NodeStatus.ALLOCATED, NodeStatus.BROKEN):
            # This means the machine has already been commissioned, only do it if force = yes
            if force:
                # Set the machine to commission and don't wait
                if scripts:
                    maas_machine.commission(
                        wait=False, commissioning_scripts=scripts)
                    changed = True
                else:
                    maas_machine.commission(wait=False)
                    changed = True
            else:  # force = no
                module.fail_json(
                    msg='ERROR: machine is in %s state, set force: true to commission the node.' % maas_status, **result)
        elif maas_status_id == NodeStatus.DEPLOYED:
            if force:
                maas_machine.release(wait=True)
                maas_machine.commission(wait=False)
                changed = True
            else:
                module.fail_json(
                    msg='ERROR: machine is in %s state, set force: true to commission the node.' % maas_status, **result)
        elif maas_status_id in (NodeStatus.COMMISSIONING, NodeStatus.DEPLOYING):
            if force:
                maas_machine.abort()
                time.sleep(20)
                maas_machine.commission(wait=False)
                changed = True
            else:
                module.fail_json(
                    msg='ERROR: machine is in %s state, set force: true to commission the node.' % maas_status, **result)
        else:
            module.fail_json(
                msg='ERROR: machine is in %s state - cannot be commissioned.' % maas_status, **result)
    if state == 'ready':
        # This action, which includes the 'Power off' action,
        # releases a node back into the pool of available nodes,
        # changing a node's status from 'Deployed' (or 'Allocated') to 'Ready'.
        try:
            if maas_status_id in (NodeStatus.ALLOCATED, NodeStatus.DEPLOYING, NodeStatus.DEPLOYED):
                # This is an ok state to release the node from
                maas_machine.release()
                changed = True
            elif maas_status_id == NodeStatus.READY:
                changed = False
        except (CallError):
            module.fail_json(
                msg='ERROR: machine is in %s state - cannot be released.' % maas_status, **result)
    if state == 'deployed':
        if maas_status_id in (NodeStatus.DEPLOYED, NodeStatus.DEPLOYING):
            if force:
                maas_machine.release(wait=True)
                time.sleep(30)
                maas_machine.refresh()
                maas_status_id = maas_machine.status
                changed = True
        if maas_status_id in (NodeStatus.READY, NodeStatus.ALLOCATED):
            # Ensure correct storage layout and boot disk
            clear_storage_result = set_storage_layout(
                system_id, maas_url, maas_apikey, 'blank')
            if 'success' in clear_storage_result:
                changed = True
            if boot_disk:
                set_boot_disk_result = set_boot_disk(maas_machine, boot_disk)
                if 'fail' in set_boot_disk_result:
                    module.fail_json(
                        msg='No physical disk found with name or serial number matching %s' % boot_disk, **result)
            if storage_layout:
                set_storage_result = set_storage_layout(
                    system_id, maas_url, maas_apikey, storage_layout)
                if 'success' in set_storage_result:
                    changed = True
                elif 'fail' in set_storage_result:
                    module.fail_json(
                        msg='Unable to apply the %s layout, please check the server in MAAS.' % storage_layout, **result)
            # Configure the networking
            delete_interfaces(maas_machine)
            if vlans:
                for vlan in vlans:
                    for key, value in vlan.items():
                        if 'state' in key:
                            vlan_state = value
                    if 'present' in vlan_state:
                        create_vlan_interface(maas_machine, vlan, maas)
                    # elif 'absent' in vlan.state:
                    #     delete_vlan_interface(maas_machine, vlan, maas)
            # This is OK to deploy
            if user_data and distro_series:
                try:
                    maas_machine.deploy(user_data=user_data,
                                        distro_series=distro_series)
                    changed = True
                except CallError as e:
                    module.fail_json(msg=e, **result)
            elif distro_series and (user_data is None):
                try:
                    maas_machine.deploy(distro_series=distro_series)
                    changed = True
                except CallError as e:
                    module.fail_json(msg=e, **result)
            elif user_data and (distro_series is None):
                try:
                    maas_machine.deploy(user_data=user_data)
                    changed = True
                except CallError as e:
                    module.fail_json(msg=e, **result)
            else:
                try:
                    maas_machine.deploy()
                    changed = True
                except (CallError):
                    module.fail_json(
                        msg='Deploy failed - check the machine config, e.g. storage is mounted correctly.', **result)
        else:
            module.fail_json(
                msg='ERROR: machine is in %s state - cannot be deployed.' % maas_status, **result)

    if module.check_mode:
        module.exit_json(**result)

    result = {"changed": changed, "system_id": system_id,
              "original_state": maas_status}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
