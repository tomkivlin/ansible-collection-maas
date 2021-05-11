#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: maas_hostname

short_description: Set MaaS machine name

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.2.3"

description: Sets the hostname for a machine in MaaS from a given device ID

options:
    hostname:
        description: Hostname to be configured.
        required: true
        type: str
    domain:
        description: Domain name for the machine to be configured.
        required: true
        type: str
    system_id:
        description: The system_id of the machine to be configured.
        required: true
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
#     - gtlabs.maas.maas_hostname

author:
    - Tom Kivlin (@tomkivlin)
'''

EXAMPLES = r'''
# Set the hostname
- name: Set the hostname
  tomkivlin.maas.maas_hostname:
    hostname: server1
    domain: foo.bar
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf

# Set the hostname, using environment variables for the URL and API key
- name: Test with a message and changed output
  tomkivlin.maas.maas_hostname:
    hostname: server1
    domain: foo.bar
    system_id: y3b3x3
'''

RETURN = r'''
# Default return values
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


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        hostname=dict(type='str', required=True),
        domain=dict(type='str', required=True),
        system_id=dict(type='str', required=True),
        maas_url=dict(type='str', required=False),
        maas_apikey=dict(type='str', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_hostname='',
        original_domain='',
        hostname='',
        domain=''
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
    changed = False

    maas = connect(maas_url, apikey=maas_apikey)

    try:
        maas_machine = maas.machines.get(system_id=system_id)
    except IndexError:
        module.fail_json(msg='No machine matching system ID %s in MaaS!' % system_id, **result)

    maas_machine_name = maas_machine.hostname
    maas_machine_domain = maas_machine.domain.name

    if domain == maas_machine_domain and hostname == maas_machine_name:
        changed = False
    else:
        if domain != maas_machine_domain:
            maas_domains = maas.domains.list()
            domain_found = 0
            for maas_domain in maas_domains:
                if maas_domain.name == domain:
                    # the provided domain is configured within MAAS
                    domain_found = 1
                    domain_obj = maas_domain
            if domain_found == 0:
                module.fail_json(msg='No domain matching name %s in MaaS!' % domain, **result)
            else:
                maas_machine.domain = domain_obj
                maas_machine.save()
                changed = True
        if hostname != maas_machine_name:
            maas_machine.hostname = hostname
            maas_machine.save()
            changed = True

    if module.check_mode:
        module.exit_json(**result)

    result = {"changed": changed, "original_hostname": maas_machine_name, "original_domain": maas_machine_domain, "hostname": hostname, "domain": domain}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
