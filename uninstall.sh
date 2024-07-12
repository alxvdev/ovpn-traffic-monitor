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
echo -e "${BLUE}  __/ / /_   ${PLAIN}${DIM}bash uninstall script${PLAIN}"
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

read -p "Are you sure you want to remove ovpn-traffic-monitor? (y/n) > " confirm

confirm=$(echo "$confirm" | tr '[:upper:]' '[:lower:]')

if [[ "$confirm" == "y" || "$confirm" == "yes" || "$confirm" == 'д' || "$confirm" == "да" ]]; then
	echo -e "${YELLOW}Removing ovpn-traffic-monitor...${PLAIN}"
else
	echo -e "${RED}Operation cancelled.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Updating package lists...${PLAIN}"
apt update -qq > /dev/null 2>&1

echo -e "${BLUE}Removing core dependencies...${PLAIN}"
apt remove -y -qq  \
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
	echo -e "${GREEN}Core dependencies removed successfully.${PLAIN}"
else
	echo -e "${RED}Error removing core dependencies.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Removing additional dependencies...${PLAIN}"
pip3 uninstall -q --no-cache-dir \
	rich \
	watchdog \
	configparser\
	asyncio \
	--break-system-packages > /dev/null 2>&1

if [[ $? -eq 0 ]]; then
	echo -e "${GREEN}Additional dependencies removing successfully.${PLAIN}"
else
	echo -e "${RED}Error removing additional dependencies.${PLAIN}"
	exit 1
fi

echo -e "${BLUE}Delete systemd service...${PLAIN}"

SERVICE_FILE="/etc/systemd/system/ovpn-traffic-monitor.service"
rm -rf "$SERVICE_FILE"

echo -e "${BLUE}Reload systemd...${PLAIN}"
systemctl daemon-reload

echo -e "${GREEN}All required dependencies have been removed.${PLAIN}"
