#!/bin/bash

SERVICE_NAME="ovpn-traffic-monitor.service"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PLAIN='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

echo -e "${BLUE}     ____    ${GREEN}${BOLD}ovpn-traffic-monitor${PLAIN}"
echo -e "${BLUE}  __/ / /_   ${PLAIN}${DIM}service status bash script${PLAIN}"
echo -e "${BLUE} /_  . __/   ${PLAIN}${DIM}for openvpn user traffic monitor${PLAIN}"
echo -e "${BLUE}/_    __/    ${CYAN}${DIM}maintained by alxvdev${PLAIN}"
echo -e "${BLUE} /_/_/       ${CYAN}https://github.com/alxvdev/ovpn-traffic-monitor${PLAIN}"

check_service_status() {
	local status=$(systemctl is-active "$SERVICE_NAME")

	case "$status" in
		"active")
			echo -e "${GREEN}Service $SERVICE_NAME is active and running.${PLAIN}"
			;;
		"inactive")
			echo -e "${RED}Service $SERVICE_NAME is inactive and not running.${PLAIN}"
			;;
		"failed")
			echo -e "${RED}Service $SERVICE_NAME has failed.${PLAIN}"
			echo -e "${YELLOW}Showing journalctl logs:${PLAIN}"
			journalctl -feu "$SERVICE_NAME" 
			;;
		"waiting")
			echo -e "${YELLOW}Service $SERVICE_NAME is in a waiting state, there might be some issues.${PLAIN}"
			;;
		*)
			echo -e "${RED}Service $SERVICE_NAME does not exist. Please run the script with the --install flag.${PLAIN}"
			;;
	esac
}

install_service() {
	echo -e "${BLUE}Installing and starting service $SERVICE_NAME${PLAIN}"
	bash install.sh
}

restart_service() {
	echo -e "${BLUE}Restarting service $SERVICE_NAME...${PLAIN}"
	systemctl restart "$SERVICE_NAME"
}

stop_service() {
	echo -e "${BLUE}Stopping service $SERVICE_NAME...${PLAIN}"
	systemctl stop "$SERVICE_NAME"
}

enable_service() {
	echo -e "${BLUE}Enabling service $SERVICE_NAME...${PLAIN}"
	systemctl enable "$SERVICE_NAME"
}

disable_service() {
	echo -e "${BLUE}Disabling service $SERVICE_NAME...${PLAIN}"
	systemctl disable "$SERVICE_NAME"
}

get_service_info() {
	echo -e "${CYAN}Service name:$SERVICE_NAME${PLAIN}"
	systemctl status "$SERVICE_NAME"
}

case "$1" in
	"--install")
		install_service
		;;
	"--restart")
		restart_service
		;;
	"--stop")
		stop_service
		;;
	"--enable")
		enable_service
		;;
	"--disable")
		disable_service
		;;
	"--get")
		get_service_info
		;;
	*)
		check_service_status
		;;
esac
