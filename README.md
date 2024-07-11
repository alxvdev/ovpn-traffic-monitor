# ovpn-traffic-monitor
OpenVPN Client Traffic monitor

```
  ____              _   _____  _  __    ovpn-traffic-monitor
 / __ \___  ___ ___| | / / _ \/ |/ /    script for managing openvpn users
/ /_/ / _ \/ -_) _ \ |/ / ___/    /     and monitoring their network traffic
\____/ .__/\__/_//_/___/_/  /_/|_/      maintained by alxvdev
    /_/                                 https://github.com/alxvdev/ovpn-traffic-monitor

usage: traffic_monitor.py [-h] [--config CONFIG]
                          [--add REAL_IP VIRTUAL_IP COMMON_NAME] [--delete REAL_IP]

OpenVPN Traffic Monitor

options:
  -h, --help            show this help message and exit
  --config CONFIG       Path to the configuration file
  --add REAL_IP VIRTUAL_IP COMMON_NAME
                        Add a new user
  --delete REAL_IP      Delete an existing user
```

## Configuration
Example `config.ini` file:

```ini
[PATHS]
openvpn_status_file=/var/log/openvpn-status.log
users_file=/var/log/ovpn-users.json
traffic_monitor_log=/var/log/ovpn-traffic.log

[LOGGING]
log_file=/var/log/wavevpn.log

[MONITOR]
network_interface=tun0
monitoring_sites=bbc.com,www.google.ru
```

## Installing
Add/edit this strings to `/etc/openvpn/server.conf`:

```conf
duplicate-cn
status /var/log/openvpn-status.log
log-append /var/log/openvpn-log.log
verb 4
```

Clone repo and launch script:

```bash
git clone https://github.com/alxvdev/ovpn-traffic-monitor ~/ovpn-traffic-monitor
cd ovpn-traffic-monitor
chmod +x install.sh
./install.sh
```

All done!
