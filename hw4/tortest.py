import io
import pycurl
from StringIO import StringIO

import stem.process

from stem.util import term

SOCKS_PORT = 7000

def query(url):
	buffer = StringIO()
	
	query = pycurl.Curl()
	query.setopt(pycurl.URL, url)
	query.setopt(pycurl.PROXY, 'localhost')
	query.setopt(pycurl.PROXYPORT, SOCKS_PORT)
	query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
	query.setopt(pycurl.WRITEFUNCTION, buffer.write)

	try:
		query.perform()
		return buffer.getvalue()
	except pycurl.error as exc:
		return "Unable to read %s (%s)" % (url, exc)


def print_bootstrap_lines(line):
	if "Bootstrapped " in line:
		print(term.format(line, term.Color.RED))

print("Launching Tor:\n")


tor_process = stem.process.launch_tor_with_config(
	config = {
		'SocksPort': str(SOCKS_PORT),
		'ExitNodes': '{ru}',
	},
	init_msg_handler = print_bootstrap_lines,
)

print("\nChecking our endpoint:\n")
print(query("http://www.nytimes.com/"))

print("\nKilling Tor process...\n")

tor_process.kill()

print ("\nExecution complete.\n")
