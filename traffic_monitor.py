#!venv/bin/python3
# -*- coding:utf-8 -*-
"""
OVPN Client Traffic Monitor.
This script manages OpenVPN users, including adding, deleting and monitoring their traffic.
It uses the OpenVPN stus log to get user information and tcpdump to monitor user traffic.
The user data is stored in a JSON file, and the script logs any visits to monitored websites.

Copyright (c) 2024 Alexeev Bronislav

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from threading import Thread
import subprocess
import uuid
import json
import datetime
import argparse
import socket
import logging
from pathlib import Path
from configparser import ConfigParser
from rich import print

LOGO = '''
[blue]  ____              _   _____  _  __    [/blue][green bold]ovpn-traffic-monitor[/green bold]
[blue] / __ \\___  ___ ___| | / / _ \\/ |/ /    [/blue][dim italic]script for managing openvpn users[/dim italic]
[blue]/ /_/ / _ \\/ -_) _ \\ |/ / ___/    /     [/blue][dim italic]and monitoring their network traffic[/dim italic]
[blue]\\____/ .__/\\__/_//_/___/_/  /_/|_/      [/blue][cyan dim]maintained by alxvdev[/cyan dim]
[blue]    /_/                                 [/blue][cyan]https://github.com/alxvdev/ovpn-traffic-monitor[/cyan]
'''


def msg(msg_text: str, msg_type: str) -> str:
	"""
	Print message withour logging

	:param msg_text: Text of message
	:param msg_type: Type of message

	:return: Message with rich formatting
	"""
	msg_type = msg_type.lower()
	if msg_type == 'info' or msg_type == logging.INFO:
		message = f'[green]{datetime.datetime.now()}::INFO[/green] -- {msg_text}'
	elif msg_type == 'warning' or msg_type == logging.WARNING:
		message = f'[yellow]{datetime.datetime.now()}::WARNING[/yellow] -- {msg_text}'
	elif msg_type == 'error' or msg_type == logging.ERROR:
		message = f'[red]{datetime.datetime.now()}::ERROR[/red] -- {msg_text}'
	else:
		message = f'[blue]{datetime.datetime.now()}::{msg_type.upper()}[/blue] -- {msg_text}'

	print(message)

	return message


class Config:
	"""
	Holds the configuration for the application.
	"""
	def __init__(self, config_file: str='config.ini'):
		if not Path(config_file).exists():
			msg(f'Configuration file "{config_file}" does not exist', 'error')
			exit(1)

		try:
			self.config = ConfigParser()
			self.config.read(config_file)
		except Exception as ex:
			msg(f'Error occurred when reading config file {config_file}: {ex}', 'error')
			exit(1)

		# Paths
		self.OPENVPN_STATUS_FILE = self.config.get('PATHS', 'openvpn_status_file')
		self.USERS_JSON_FILE = self.config.get('PATHS', 'users_file')
		self.TRAFFIC_LOG = self.config.get('PATHS', 'traffic_monitor_log')

		print(f'OpenVPN Status File: {self.OPENVPN_STATUS_FILE}')
		print(f'OpenVPN Users JSON Data: {self.USERS_JSON_FILE}')
		print(f'User traffic log: {self.TRAFFIC_LOG}')

		# Logging
		self.LOG_FORMAT = "[%(asctime)s %(levelname)s] %(name)s -- %(message)s"
		self.LOG_FILEPATH = self.config.get('LOGGING', 'log_file')

		print(f'Plain logging format string: {self.LOG_FORMAT}')
		print(f'Plain log filepath: {self.LOG_FILEPATH}')

		# Monitor
		self.NETWORK_INTERFACE = self.config.get('MONITOR', 'network_interface')
		self.MONITORING_SITES = [site.strip() for site in self.config.get('MONITOR', 'monitoring_sites').split(',')]

		print(f'Network interface of OpenVPN: {self.NETWORK_INTERFACE}')
		print(f'Monitoring sites list: {self.MONITORING_SITES}')


class TrafficMonitorLogger:
	"""
	Responsible for logging website visits
	"""
	@staticmethod
	def log_website_visit(real_ip: str, virtual_ip: str, user_uuid: str, website: str) -> None:
		"""
		Log a website visit

		:param real_ip: Real user IP Address
		:param virtual_ip: Virtual user IP Address in network
		:param user_uuid: Universal Unique Identifier
		:param website: Website URL
		"""
		timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		log_entry = f'[{timestamp}] {user_uuid} ({virtual_ip}/{real_ip}) visited the site {website}'
		print(log_entry)

		with open(Config().TRAFFIC_LOG, 'a') as file:
			file.write(f'{log_entry}\n')


class PlainLogger:
	"""
	Plain Logger system
	"""
	def __init__(self, logfilename: str, formatting: str):
		"""
		PlainLogger initialization

		:param logfilename: Logfile path
		:param formatting: Formatting string
		"""
		self.logfilename = logfilename
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.DEBUG)

		handler = logging.FileHandler(logfilename, mode='w')
		formatter = logging.Formatter(formatting)

		handler.setFormatter(formatter)
		self.logger.addHandler(handler)

	def get_logger(self) -> logging.Logger:
		"""
		Get logger object
		"""
		return self.logger

	def log(self, text: str, message_type: str='info'):
		"""
		Logging messages

		:param text: Text of message
		:param message_type: Type of message (info, warning, error or other)
		"""
		message_type = message_type.upper()

		if message_type == logging.INFO or message_type == 'info':
			msg(text, message_type)
			self.logger.info(text)
		if message_type == logging.WARNING or message_type == 'warning':
			msg(text, message_type)
			self.logger.warning(text)
		if message_type == logging.ERROR or message_type == 'error':
			msg(text, message_type)
			self.logger.error(text)
		else:
			msg(text, message_type)
			self.logger.info(text)


class TCPDumpManager:
	"""
	Manages the tcpdump processes for monitoring user traffic
	"""
	def __init__(self, plain_logger: PlainLogger, config: Config):
		"""
		Initialization TCPDump Manager

		:param plain_logger: PlainLogger object
		:param config: Config object
		"""
		self.active_processes: dict = {}
		self.logger = plain_logger
		self.config = config

	def get_hostname_from_ip(self, ip_address: str) -> str:
		"""
		Get hostname by ip address

		:param ip_address: IP Address of server for resolving hostname

		:return: Hostname or N/A
		"""
		try:
			hostname, aliaslist, ipaddrlist = socket.gethostbyaddr(ip_address)
			return hostname
		except socket.herror as e:
			self.logger.log(f'Error resolving hostname for IP Address {ip_address}: {e}', 'warning')
			return "N/A"

	def traffic_logging(self, process_data: dict) -> None:
		"""
		Method for traffic logging.

		:param process_data: Dictionary with process, user virtual ip, user real ip and user uuid
		"""
		process = process_data['process']

		try:
			while True:
				output = process.stdout.readline()

				if output == b'' and process.poll() is not None:
					print('Stop monitoring user traffic...')
					break
				else:
					output = output.decode()
					try:
						website = output.split(' ')[4].split('.')
						website = '.'.join(website[:-1]).strip()
					except Exception:
						continue
					
					if website == process_data['virtual_ip']:
						continue

				print(f'Traffic detected {process_data["uuid"]}: {process_data["virtual_ip"]}/{process_data["real_ip"]} -> {self.get_hostname_from_ip(website)} ({self.get_hostname_from_ip(website)})')
				TrafficMonitorLogger.log_website_visit(process_data['real_ip'], process_data['virtual_ip'], process_data['uuid'], f'{website}/{self.get_hostname_from_ip(website)}')
		except Exception:
			self.logger.log('Error occurred during the operation of the traffic logging thread (uncritical, but atypical)', 'warning')
			return

		return

	def monitor_user_traffic(self, user_uuid: str, real_ip: str, virtual_ip: str) -> None:
		"""
		Start monitoring user traffic

		:param user_uuid: User Universal Unique Identifier
		:param real_ip: user real IP Address
		:param virtual_ip: user virtual IP Address
		"""
		try:
			tcpdump_filter = f'src {virtual_ip}'
			process = subprocess.Popen(['tcpdump', '-i', self.config.NETWORK_INTERFACE, '-U' '-n', tcpdump_filter],
										stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			self.logger.log(f'Executing a command to monitor network traffic: tcpdump -i {self.config.NETWORK_INTERFACE} -U -n {tcpdump_filter}', 'info')

			if process.returncode == 1:
				self.logger.log(f'An error occurred during the command to start the traffic monitoring process: {process.stderr}', 'error')
				exit(1)

			process_data = {
				'process': process,
				'virtual_ip': virtual_ip,
				'uuid': user_uuid,
				'real_ip': real_ip,
			}

			thread_monitor = Thread(target=self.traffic_logging, args=(process_data,))

			try:
				thread_monitor.start()
				thread_monitor.join()
			except Exception as ex:
				self.logger.log(f'Warning (must be error) occurred when starting thread: {ex}', 'warning')
			else:
				self.logger.log(f'Start user traffic monitoring thread ({user_uuid}) successfully', 'debug')

			process_data['thread'] = thread_monitor
			self.active_processes[real_ip] = process_data
		except Exception as ex:
			self.logger.log(f'Error occurred when start monitor user traffic thread: {ex}', 'error')

	def stop_user_traffic_monitoring(self, user_ip: str) -> None:
		"""
		Stop monitoring user traffic.

		:param user_ip: User Real IP Address
		"""
		if user_ip in self.active_processes:
			try:
				self.logger.log(f'Stop user traffic monitoring: {user_ip}', 'info')
				process = self.active_processes[user_ip]['process']
				process.terminate()
				self.logger.log(f'Terminated user traffic monitoring process ({user_ip})', 'debug')
				thread = self.active_processes[user_ip]['thread']
				thread.stop()
				self.logger.log(f'Stopped user traffic monitoring thread ({user_ip})', 'debug')
				del self.active_processes[user_ip]
			except Exception as ex:
				self.logger.log(f'Error occurred when stopping user traffic monitoring: {ex}', 'warning')


class OpenVPNUserManager:
	"""
	Class for managing openvpn users
	"""
	def __init__(self, tcpdump_manager: TCPDumpManager, config: Config, plain_logger: PlainLogger):
		"""
		Initialization

		:param tcpdump_manager: TCPDump Manager object
		:param config: Config object
		:param plain_logger: Plain Logger object
		"""
		self.tcpdump_manager: TCPDumpManager = tcpdump_manager
		self.config: Config = config
		self.users_data: dict = {}
		self.logger: PlainLogger = plain_logger

	def parse_openvpn_users(self) -> list:
		"""
		Parse the OpenVPN status log and return user information

		:return: List of users
		"""
		lines = []
		result = []
		users = []
		include = False

		try:
			try:
				with open(self.config.OPENVPN_STATUS_FILE, 'r') as file:
					for line in file.read().strip().split('\n'):
						lines.append(line)
			except FileNotFoundError:
				self.logger.log(f'File not found: {self.config.OPENVPN_STATUS_FILE}', 'error')
				exit(1)
			except PermissionError:
				self.logger.log(f'Permission error: {self.config.OPENVPN_STATUS_FILE}', 'error')
				exit(1)

			for line in lines:
				if line == "Virtual Address,Common Name,Real Address,Last Ref":
					include = True
					continue

				if include:
					if line == "GLOBAL STATS":
						include = False
						continue
					line = line.replace(line.split(',')[2], line.split(',')[2].split(':')[0])
					result.append(line)

			for res_i in result:
				users.append([user for user in res_i.split(',')])

			return users
		except Exception as ex:
			self.logger.log(f'Error when parsing openvpn users: {ex}', 'error')
			exit(1)

		return users

	def update_user_data(self, users: list=None) -> list:
		"""
		Update user JSON data

		:param users: Users list (if is None, parse users)

		:return: List of users
		"""
		if users is None:
			users = self.parse_openvpn_users()

		for user in users:
			self.users_data[user[2]] = {
				'uuid': str(uuid.uuid4()),
				'virtual_ip': user[0],
				'real_ip': user[2],
				'common_name': user[1]
			}

			try:
				with open(self.config.USERS_JSON_FILE, 'w') as f:
					json.dump(self.users_data, f, indent=4)
			except IOError:
				self.logger.log(f'Error: Could not write to {self.config.USERS_JSON_FILE}', 'error')

		return self.users_data

	def update_user_monitoring(self) -> None:
		"""
		Update the tcpdump monitoring for users
		"""
		users_list = self.parse_openvpn_users() # list[list] of users
		users_data = self.update_user_data(users_list) # dict of users

		try:
			for user in users_list:
				real_ip = user[2]
				virtual_ip = users_data[real_ip]['virtual_ip']
				# common_name = users_data[real_ip]['common_name']
				user_uuid = users_data[real_ip]['uuid']

				if real_ip not in self.tcpdump_manager.active_processes:
					thread_monitor = Thread(target=self.tcpdump_manager.monitor_user_traffic, args=(user_uuid, real_ip, virtual_ip))
					thread_monitor.start()
					thread_monitor.join()
		except Exception as ex:
			self.logger.log(f'Error when start active user monitoring threads: {ex}', 'error')
			exit(1)

		try:
			for user in users_list:
				try:
					data = self.tcpdump_manager.active_processes[user[2]]
					self.logger.log(f'User connected ({data["uuid"]}: {data["virtual_ip"]}/{data["real_ip"]}')
				except KeyError:
					self.tcpdump_manager.stop_user_traffic_monitoring(user[2])
		except Exception as ex:
			self.logger.log(f'Error when stop inactive user monitoring threads: {ex}', 'error')
			exit(1)


	def add_user(self, real_ip: str, virtual_ip: str, common_name: str) -> None:
		"""
		Add a new user

		:param user_uuid: User Universal Unique Identifier
		:param real_ip: user real IP Address
		:param virtual_ip: user virtual IP Address
		:param common_name: common name of client .ovpn config
		"""
		self.users_data[real_ip] = {
			'uuid': str(uuid.uuid4()),
			'virtual_ip': virtual_ip,
			'real_ip': real_ip,
			'common_name': common_name
		}

		try:
			with open(self.config.USERS_JSON_FILE, 'w') as f:
				json.dump(self.users_data, f, indent=4)
		except IOError:
			self.logger.log(f'Error: Could not write to {self.config.USERS_JSON_FILE}', 'error')
		else:
			self.logger.log(f'User {real_ip}/{virtual_ip} has been created', 'debug')

	def delete_user(self, real_ip: str) -> None:
		"""
		Delete an existing user

		:param real_ip: user real ip address
		"""
		if real_ip in self.users_data:
			self.logger.log(f'User {real_ip} has been deleted', 'debug')
			self.tcpdump_manager.stop_user_traffic_monitoring(real_ip)
			del self.users_data[real_ip]

			try:
				with open(self.config.USERS_JSON_FILE, 'w') as f:
					json.dump(self.users_data, f, indent=4)
			except IOError:
				self.logger.log(f'Error: Could not write to {self.config.USERS_JSON_FILE}', 'error')


def main():
	"""
	Main function
	"""
	print(LOGO)

	parser = argparse.ArgumentParser(description='OpenVPN Traffic Monitor')
	parser.add_argument('--config', default='/root/ovpn-traffic-monitor/config.ini', help='Path to the configuration file')
	parser.add_argument('--add', nargs=3, metavar=('REAL_IP', 'VIRTUAL_IP', 'COMMON_NAME'), help='Add a new user')
	parser.add_argument('--delete', metavar='REAL_IP', help='Delete an existing user')

	args = parser.parse_args()

	msg('Load Config Module...', 'debug')
	try:
		config = Config(args.config)
	except Exception as ex:
		msg(f'Fail to load config module: {ex}', 'error')
		exit(1)
	else:
		msg('Successfully load Config Module!', 'info')

	msg('Load PlainLogger module...', 'debug')
	try:
		logger = PlainLogger(config.LOG_FILEPATH, config.LOG_FORMAT)
	except Exception as ex:
		msg(f'Fail to load PlainLogger module: {ex}', 'error')
		exit(1)
	else:
		msg('Successfully load Config Module!', 'info')

	logger.log(f'Config: {args.config}', 'debug')

	logger.log('Load TCPDump Manager module...', 'debug')
	try:
		tcpdump_manager = TCPDumpManager(logger, config)
	except Exception as ex:
		logger.log(f'Fail to load TCPDump Manager module: {ex}', 'error')
		exit(1)
	else:
		logger.log('Successfully load TCPDump Manager Module!', 'info')

	logger.log('Load OpenVPN User Manager module...', 'debug')
	try:
		openvpn_user_manager = OpenVPNUserManager(tcpdump_manager, config, logger)
	except Exception as ex:
		logger.log(f'Fail to load OpenVPN User Manager module: {ex}', 'error')
		exit(1)
	else:
		logger.log('Successfully load OpenVPN User Manager Module!', 'info')

	if args.add:
		real_ip, virt_ip, common_name = args.add
		openvpn_user_manager.add_user(real_ip, virt_ip, common_name)
		exit(1)
	elif args.delete:
		openvpn_user_manager.delete_user(args.delete)
		exit(1)

	logger.log('Initial update user monitoring', 'debug')
	try:
		openvpn_user_manager.update_user_monitoring()
	except Exception as ex:
		logger.log(f'Error occurred when update user monitoring: {ex} ', 'error')
		exit(1)
	else:
		logger.log('Successfully updated!', 'info')

	logger.log('Initial update user data', 'debug')
	try:
		openvpn_user_manager.update_user_data()
	except Exception as ex:
		logger.log(f'Error occurred when update user data: {ex} ', 'error')
		exit(1)
	else:
		logger.log('Successfully updated!', 'info')

	logger.log('Start program loop...', 'debug')
	while True:
		try:
			openvpn_user_manager.update_user_monitoring()
			openvpn_user_manager.update_user_data()
		except KeyboardInterrupt:
			print('[yellow]Get KeyboardInterrupt: stop...[/yellow]')
			break
		except Exception as ex:
			logger.log(f'Error: {ex}', 'error')
			break

	logger.log('Stop program loop...', 'debug')


if __name__ == '__main__':
	main()
