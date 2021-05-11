# ansible-collection-maas <!-- omit in toc -->
Ansible collection of modules to use in IaC management of MAAS-managed infrastructure.

Requires the [python-libmaas](https://github.com/maas/python-libmaas) library to be installed on the Ansible control node.  This has been tested using `python-libmaas==0.6.6`.

## Modules <!-- omit in toc -->
- "info" modules:
  - `maas_machine_info`
    - Gets all info about a machine in MaaS from the system_id or hostname
  - `maas_system_id_info`
    - Gets system_id from hostname or power_address
  - `maas_machine_state_info`
    - Gets the state of a machine in MaaS from the system_id or hostname
- "action" modules:
  - `maas_hostname`
    - Sets the hostname for a machine in MaaS from a given device ID
  - `maas_machine_state`
    - Manages the state of a machine in MaaS from a given device ID or hostname