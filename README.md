# ovpn-traffic-monitor
OpenVPN Client Traffic monitor

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
git clone https://github.com/alxvdev/ovpn-traffic-monitor
cd ovpn-traffic-monitor
chmod +x install.sh
./install.sh
```

All done!
