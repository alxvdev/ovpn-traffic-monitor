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
echo -e "${BLUE}  __/ / /_   ${PLAIN}${DIM}bash install script${PLAIN}"
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

echo -e "${YELLOW}Install ovpn-traffic-monitor${PLAIN}"

echo -e "${BLUE}Updating package lists...${PLAIN}"
apt update -qq > /dev/null 2>&1

echo -e "${BLUE}Installing core dependencies...${PLAIN}"
apt install -y -qq  \
	build-essential \
	git \
	python3 \
	python3-pip \
	python3-venv \
	tcpdump \
	openvpn \
	watchdog \
	jq > /dev/null 2>&1

if [[ $? -eq 0 ]]; then
	echo -e "${GREEN}Core dependencies installed successfully.${PLAIN}"
else
	echo -e "${RED}Error installing core dependencies.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Installing additional dependencies...${PLAIN}"
pip3 install -q --no-cache-dir \
	rich \
	watchdog \
	configparser\
	asyncio \
	--break-system-packages > /dev/null 2>&1

if [[ $? -eq 0 ]]; then
	echo -e "${GREEN}Additional dependencies installed successfully.${PLAIN}"
else
	echo -e "${RED}Error installing additional dependencies.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Creating systemd service...${PLAIN}"

SERVICE_FILE="/etc/systemd/system/ovpn-traffic-monitor.service"
SCRIPT_PATH=$(realpath traffic_monitor.py)
CONFIG_PATH=$(realpath config.ini)
cat << EOF >> $SERVICE_FILE
[Unit]
Description=OpenVPN Client Traffic Monitor
After=network.target openvpn.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 $SCRIPT_PATH --config $CONFIG_PATH
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

echo -e "${BLUE}Enabling and starting systemd service...${PLAIN}"
systemctl daemon-reload
systemctl enable ovpn-traffic-monitor
systemctl start ovpn-traffic-monitor

echo -e "${GREEN}All required dependencies have been installed and the systemd has been set up.${PLAIN}"
echo -e "${GREEN}The traffic monitor python script will now run automatically on system boot.${PLAIN}"

echo -e "${YELLOW}systemd service file: $SERVICE_FILE${PLAIN}"
