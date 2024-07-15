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
import traceback
import datetime
import platform
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text as RText


def get_local_time() -> str:
	"""
	Get local time

	:return: Local strftime (year-month-day hours:minutes:seconds)
	"""
	return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class ExceptionLevel(Enum):
	"""
	Exception level
	"""
	EXCEPTION_BASE_LEVEL = 0
	EXCEPTION_UNCRITICAL_LEVEL = 1
	EXCEPTION_WARNING_LEVEL = 2
	EXCEPTION_ERROR_LEVEL = 3
	EXCEPTION_CRITICAL_LEVEL = 4


class ExceptionCategory(Enum):
	EXCEPTION_GENERAL_CATEGORY = "General"
	EXCEPTION_IO_CATEGORY = "I/O"
	EXCEPTION_THREAD_CATEGORY = "Multithreading"
	EXCEPTION_MODULE_CATEGORY = "Python Module"
	EXCEPTION_CLASS_CATEGORY = "Class Object"
	EXCEPTION_NETWORK_CATEGORY = "Network (socket)"
	EXCEPTION_STDOUT_CATEGORY = "STDOUT/STDERR (output)"
	EXCEPTION_PERMISSION_CATEGORY = "Permission"
	EXCEPTION_UNKNOWN_CATEGORY = "Unknown"


def exception_explaination_by_errorcode(error_code: str) -> str:
	ex_level = int(error_code.split(':::')[0].strip())
	ex_category = error_code.split(':::')[1].strip()

	explaination = ''

	match ex_level:
		case 0:
			ex_level = ExceptionLevel.EXCEPTION_BASE_LEVEL
			explaination = 'The exception is [blue]basic[/blue] in terms of criticality. The basic exception does [blue bold]not pose a danger[/blue bold] to the operation of the software.'
		case 1:
			ex_level = ExceptionLevel.EXCEPTION_WARNING_LEVEL
			explaination = 'The exception is [cyan]uncritical[/cyan] in terms of criticality. The uncritical exception [cyan bold]does not pose a danger[/cyan bold] to the operation of the software, but it can [italic]provide useful information.[/italic]'
		case 2:
			ex_level = ExceptionLevel.EXCEPTION_UNCRITICAL_LEVEL
			explaination = 'The exception is [yellow]warning[/yellow] in terms of criticality. The warning exception [yellow bold]does not pose a danger[/yellow bold] to the operation of the software, [italic]but the software may have a bug or problem.[/italic]'
		case 3:
			ex_level = ExceptionLevel.EXCEPTION_ERROR_LEVEL
			explaination = 'The exception is [bold red]error[/bold red] in terms of criticality. The error exception [red bold]pose a danger[/red bold] to the operation of the software.'
		case 4:
			ex_level = ExceptionLevel.EXCEPTION_ERROR_LEVEL
			explaination = 'The exception is [underline bold red]critical[/underline bold red] error in terms of criticality. The critical error exception [red underline bold]pose a serious danger[/red underlinebold] to the operation of the software.'
		case _:
			explaination = "Unknown exception level in terms of criticality."

	match ex_category:
		case "I/O":
			ex_category = ExceptionCategory.EXCEPTION_IO_CATEGORY
			explaination += ' Category of exception: [underline bold]I/O (input/output)[/underline bold]. This type of exception occurs when there are problems [red italic]writing of reading data from disk.[/red italic]'
		case "Multithreading":
			ex_category = ExceptionCategory.EXCEPTION_THREAD_CATEGORY
			explaination += ' Category of exception: [underline bold]Multithreading[/underline bold]. This type of exception occurs when there are problems working with [red italic]threads.[/red italic]'
		case "Python Module":
			ex_category = ExceptionCategory.EXCEPTION_MODULE_CATEGORY
			explaination += ' Category of exception: [underline bold]python module (or package)[/underline bold]. This type of exception occurs when there are problems with [red italic]python packages or modules.[/red italic]'
		case "Class Object":
			ex_category = ExceptionCategory.EXCEPTION_CLASS_CATEGORY
			explaination += ' Category of exception: [underline bold]python class object[/underline bold]. This type of exception occurs when there are problems with [red italic]python class objects.[/red italic]'
		case "Network (socket)":
			ex_category = ExceptionCategory.EXCEPTION_NETWORK_CATEGORY
			explaination += ' Category of exception: [underline bold]Network[/underline bold]. This type of exception occurs when there are problems with [red italic]network (sockets).[/red italic]'
		case "STDOUT/STDERR (output)":
			ex_category = ExceptionCategory.EXCEPTION_STDOUT_CATEGORY
			explaination += ' Category of exception: [underline bold]STDOUT[/underline bold]. This type of exception occurs when there are problems with [red italic]stdout (subprocess commands output)[/red italic]'
		case "Permission":
			ex_category = ExceptionCategory.EXCEPTION_PERMISSION_CATEGORY
			explaination += ' Category of exception: [underline bold]Permissions[/underline bold]. This type of exception occurs when there are problems with [red italic]permissions[/red italic].'
		case "Unknown":
			ex_category = ExceptionCategory.EXCEPTION_UNKNOWN_CATEGORY
			explaination += ' Category of exception: [underline bold]Unknown[/underline bold]. This type of exception occurs when there are [red italic]unknown[/red italic] problems.'
		case "General":
			ex_category = ExceptionCategory.EXCEPTION_GENERAL_CATEGORY
			explaination += ' Category of exception: [bold]General[/bold]. This type of exception occurs when there are [red italic]general[/red italic] problems.[/italic]'

	return explaination

class BaseException(Exception):
	"""
	Base class for custom exceptions
	"""
	exception_id = "BASE_EXCEPTION"
	exception_category = ExceptionCategory.EXCEPTION_GENERAL_CATEGORY
	exception_level = ExceptionLevel.EXCEPTION_BASE_LEVEL

	def __init__(self, message: str, details: str):
		self.message = message
		self.details = details
		self.traceback_info = self.get_traceback()
		self.timestamp = get_local_time()
		self.python_version = platform.python_version()
		self.os_info = {
			'Machine': platform.machine(),
			'Node': platform.node(),
			'Proccessor': platform.processor(),
			"OS": f'{platform.system()} {platform.release()} {platform.version()}'
		}

		for key, value in platform.freedesktop_os_release().items():
			self.os_info[key] = value

	def render_exception_info(self) -> Table:
		table = Table(show_header=True, show_edge=True, padding=(0, 1))

		table.add_column("Message", style='bold red')
		table.add_column("Details", style='bold red')
		table.add_column("Timestamp", style='bold red')
		table.add_column("Python version", style='bold red')

		table.add_row(
			RText(self.message, style='bold green'),
			RText(self.details, style='bold green'),
			RText(self.timestamp, style='bold green'),
			RText(f'Python {self.python_version}', style='bold green')
		)

		return table

	def render_os_info(self) -> Panel:
		info = ''

		for key, value in self.os_info.items():
			info += f'[bold]{key}[/bold]: {value}\n'

		info += '[bold]GitHub repository[bold]: https://github.com/alxvdev/ovpn-traffic-monitor'

		return Panel(
			info,
			title='Operating System',
			border_style='bold magenta'
		)

	def render_traceback_info(self) -> Panel:
		return Panel(
			self.traceback_info,
			title='Traceback',
			border_style='bold yellow'
		)

	def get_traceback(self):
		tb = traceback.extract_stack()
		frame = tb[0]
		error_code = f"{self.exception_level.value}:::{self.exception_category.value}"
		explaination = exception_explaination_by_errorcode(error_code)
		return f'[italic]in [/italic][underline]{frame.filename}[/underline][italic] at [magenta]{frame.lineno}[/magenta]:[/italic]\n >>> [bold]{frame.line}[/bold]\n\nError code {error_code}: {explaination}'

	def __str__(self):
		console = Console()
		panel = Panel(
			self.render_exception_info(),
			title=f'[bold red]{self.exception_id} L{self.exception_level.value}: {self.exception_category.value}[/bold red]',
			border_style='bold red'
		)

		console.print(panel)
		console.print(self.render_os_info())
		console.print(self.render_traceback_info())

		console.print(f'Error code: {self.error_code}')

		if self.exception_level.value >= 3:
			exit(1)
		
		return f"{self.exception_id}"


class IOException(BaseException):
	exception_id = "IO_EXCEPTION"
	exception_category = ExceptionCategory.EXCEPTION_IO_CATEGORY
	
	def __init__(self, message: str, details: str, exception_level: ExceptionLevel):
		super().__init__(message, details)
		self.exception_level = exception_level
		self.error_code = f"{self.exception_level.value}:::{self.exception_category.value}"


class ThreadException(BaseException):
	exception_id = "THREAD_EXCEPTION"
	exception_category = ExceptionCategory.EXCEPTION_THREAD_CATEGORY
	
	def __init__(self, message: str, details: str, exception_level: ExceptionLevel):
		super().__init__(message, details)
		self.exception_level = exception_level
		self.error_code = f"{self.exception_level.value}:::{self.exception_category.value}"


class ClassObjectException(BaseException):
	exception_id = "CLASSOBJECT_EXCEPTION"
	exception_category = ExceptionCategory.EXCEPTION_CLASS_CATEGORY
	
	def __init__(self, message: str, details: str, exception_level: ExceptionLevel):
		super().__init__(message, details)
		self.exception_level = exception_level
		self.error_code = f"{self.exception_level.value}:::{self.exception_category.value}"
