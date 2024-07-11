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
echo -e "${BLUE}  __/ / /_   ${PLAIN}${DIM}bash update script${PLAIN}"
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

echo -e "${YELLOW}Update ovpn-traffic-monitor${PLAIN}"

echo -e "${BLUE}Get updates from repository (pull)...${PLAIN}"
git pull
if [[ $? -eq 0 ]]; then
	echo -e "${GREEN}Repository updated successfully.${PLAIN}"
else
	echo -e "${RED}Error updating repository.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Updating package lists...${PLAIN}"
apt update -qq > /dev/null 2>&1

echo -e "${BLUE}Upgrade packages...${PLAIN}"
apt upgrade -y -qq > /dev/null 2>&1

if [[ $? -eq 0 ]]; then
	echo -e "${GREEN}Packages updated&upgraded successfully.${PLAIN}"
else
	echo -e "${RED}Error updating packages.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Updating additional dependencies...${PLAIN}"
pip3 install -q --no-cache-dir \
	rich \
	watchdog \
	configparser\
	asyncio \
	--break-system-packages > /dev/null 2>&1

if [[ $? -eq 0 ]]; then
	echo -e "${GREEN}Additional dependencies updated successfully.${PLAIN}"
else
	echo -e "${RED}Error updating additional dependencies.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Restart systemd service...${PLAIN}"
systemctl daemon-reload
systemctl enable ovpn-traffic-monitor
systemctl start ovpn-traffic-monitor

echo -e "${GREEN}All required dependencies have been updated and the systemd has been set up.${PLAIN}"
