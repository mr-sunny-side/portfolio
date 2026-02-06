import logging

def	setting_logging():
	logging.basicConfig(
		level=logging.DEBUG,
		format='%(levelname)s - %(message)s'
	)

LOCAL_HOST = '127.0.0.1'
PORT = 8080
TIMEOUT = 30.0
BUFFER_SIZE = 4096
MAX_READ = 10 * 1024 * 1024
