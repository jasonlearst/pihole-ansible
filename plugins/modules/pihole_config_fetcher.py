#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError("The 'pihole6api' Python module is required. Run 'pip install pihole6api' to install it.")

DOCUMENTATION = r'''
---
module: pihole_config_fetcher
short_description: Fetch Pi-hole DNS configuration once for batch processing
description:
    - This module fetches both hosts and CNAME records configuration from Pi-hole in a single call
options:
    password:
        description:
            - The API password for the Pi-hole instance.
        required: true
        type: str
        no_log: true
    url:
        description:
            - The URL of the Pi-hole instance.
        required: true
        type: str
author:
    - Shane Barbetta (@sbarbett)
'''

EXAMPLES = r'''
- name: Fetch Pi-hole DNS configuration
  sbarbett.pihole.pihole_config_fetcher:
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
'''

RETURN = r'''
hosts_config:
    description: Current A/AAAA hosts configuration
    type: dict
    returned: always
cnames_config:
    description: Current CNAME records configuration  
    type: dict
    returned: always
'''

def run_module():
    module_args = dict(
        password=dict(type='str', required=True, no_log=True),
        url=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        hosts_config={},
        cnames_config={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    password = module.params['password']
    url = module.params['url']

    try:
        client = PiHole6Client(url, password)
        
        # Fetch hosts configuration
        hosts_config = client.config.get_config_section("dns/hosts")
        hosts_list = hosts_config.get("config", {}).get("dns", {}).get("hosts", [])
        
        # Parse hosts into dictionary {hostname: ip}
        hosts_dict = {}
        for entry in hosts_list:
            parts = entry.split(None, 1)
            if len(parts) == 2:
                ip, hostname = parts
                hosts_dict[hostname] = ip
        
        # Fetch CNAME configuration
        cnames_config = client.config.get_config_section("dns/cnameRecords")
        cnames_list = cnames_config.get("config", {}).get("dns", {}).get("cnameRecords", [])
        
        # Parse CNAMEs into dictionary {hostname: {target: str, ttl: int|None}}
        cnames_dict = {}
        for entry in cnames_list:
            parts = entry.split(',')
            if len(parts) >= 2:
                hostname = parts[0]
                target = parts[1]
                ttl = None
                if len(parts) == 3:
                    try:
                        ttl = int(parts[2])
                    except ValueError:
                        ttl = parts[2]
                cnames_dict[hostname] = {'target': target, 'ttl': ttl}
        
        result['hosts_config'] = hosts_dict
        result['cnames_config'] = cnames_dict
        
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error fetching Pi-hole configuration: {e}", **result)
    finally:
        if 'client' in locals() and client is not None:
            client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main()