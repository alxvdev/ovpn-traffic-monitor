#!/bin/bash

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PLAIN='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

echo -e "${BLUE}     ____    ${GREEN}${BOLD}ovpn-traffic-monitor${PLAIN}"
echo -e "${BLUE}  __/ / /_   ${PLAIN}${DIM}base config generating script${PLAIN}"
echo -e "${BLUE} /_  . __/   ${PLAIN}${DIM}for openvpn user traffic monitor${PLAIN}"
echo -e "${BLUE}/_    __/    ${CYAN}${DIM}maintained by alxvdev${PLAIN}"
echo -e "${BLUE} /_/_/       ${CYAN}https://github.com/alxvdev/ovpn-traffic-monitor${PLAIN}"
echo -e "${PLAIN}"

if ! [ -f /etc/lsb-release ] || ! grep -q "DISTRIB_ID=Ubuntu" /etc/lsb-release; then
	echo -e "${RED}This script is designed for ${BOLD}Ubuntu Linux. Exiting.${PLAIN}"
	exit 1
fi

if [[ $EUID -ne 0 ]]; then
	echo -e "${RED}This script requires superuser privileges. Run it with 'sudo'.${PLAIN}"
	exit 1
fi

echo -e "${YELLOW}Generate base config for ovpn-traffic-monitor${PLAIN}"

CURRENT_PATH=$(realpath .)
cat << EOF >> $CURRENT_PATH/config.ini
[PATHS]
openvpn_status_file=/var/log/openvpn-status.log
users_file=/var/log/ovpn-users.json
traffic_monitor_log=/var/log/ovpn-traffic.log

[LOGGING]
log_file=/var/log/wavevpn.log

[MONITOR]
network_interface=tun0
monitoring_sites=216.58.207.0/24,151.101.0.0/16,77.88.0.0/16,89.108.99.0/24
EOF

echo -e "${GREEN}Successfully generated base config for ovpn-traffic-monitor${PLAIN}"

echo -e "${BLUE}Reload systemd...${PLAIN}"

SERVICE_FILE="/etc/systemd/system/ovpn-traffic-monitor.service"

echo -e "${BLUE}Restart systemd service: $SERVICE_FILE...${PLAIN}"
systemctl daemon-reload
systemctl enable ovpn-traffic-monitor
systemctl start ovpn-traffic-monitor

echo -e "${GREEN}Base config generated!${PLAIN}"
