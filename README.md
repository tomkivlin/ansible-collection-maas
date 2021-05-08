# ansible-collection-maas <!-- omit in toc -->
Ansible collection of plugins to use in IaC management of MAAS-managed infrastructure.

## Plugins <!-- omit in toc -->
- [set_hostname](#set_hostname)
- [get_machine](#get_machine)
- [get_system_id](#get_system_id)

### set_hostname

**Description**: Sets the hostname for a machine in MaaS from a given device ID

**Options**:
```
    hostname:
        description: Hostname to be set.
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
```

**Examples**:
```
# Set the hostname
- name: Set the hostname
  tomkivlin.maas.set_hostname:
    hostname: server1
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf

# Set the hostname, using environment variables for the URL and API key
- name: Test with a message and changed output
  tomkivlin.maas.set_hostname:
    hostname: server1
    system_id: y3b3x3
```

### get_machine

**Description**: Gets all info about a machine in MaaS from the system_id or hostname

**Options**:
```
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
```

**Examples**:
```
# Get information based on the hostname
- name: Get information based on the hostname
  tomkivlin.maas.get_machine:
    hostname: server1
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf

# Get information based on the system_id
- name: Get information based on the system_id
  tomkivlin.maas.get_machine:
    system_id: y3b3x3
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
```


### get_system_id

**Description**: Gets system_id from hostname or power_address

**Options**:
```
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
```

**Examples**:
```
# Get information based on the hostname
- name: Get information about machine based on hostname
  tomkivlin.maas.get_system_id:
    hostname: server1
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf

# Get information based on the system_id
- name: Get information based on the system_id
  tomkivlin.maas.get_system_id:
    power_address: 10.1.1.100
    maas_url: http://maas_server:5240/MAAS/
    maas_apikey: fsdfsdfsdf:sdfsdfsdf:sdfsdfsdf
```
