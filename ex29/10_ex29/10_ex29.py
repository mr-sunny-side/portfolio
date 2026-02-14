#!/usr/bin/env python3

import socket
import threading
import logging

import config
from http_parse import Request, get_request, print_request

lock = threading.Lock()
config.setting_logging()

client_count = 0

"""
	02-06:	リクエストの取得まで完了
			- ハンドラーの記述から

"""

def	handle_client(client_socket, client_address):
	global client_count
	try:
		client_socket.settimeout(config.TIMEOUT)
		with lock:
			client_count += 1
			client_id = client_count
		logging.info('')
		logging.info('handle_client: Connection detected')
		logging.info(f'handle_client: {client_address[0]}:{client_address[1]}')

		# get_request呼び出し
		request_obj = Request()
		if not get_request(client_socket, request_obj):
			raise ValueError

		print_request(request_obj)

	except ValueError:
		logging.exception('handle_client: ValueError')

		# 400 bad request
	except socket.timeout:
		logging.warning('handle_client: Client timeout', exc_info=True)

		#408 request timeout
	except ConnectionError:
		logging.exception('handle_client: ConnectionError')

		# 接続切れなので送信するステータスなし
	except Exception:
		logging.exception('handle_client: Exception')

		# 500 internal server error

def	run_server(host=config.LOCAL_HOST, port=config.PORT):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	logging.info('run_server: server listening:')
	logging.info(f'run_server: {host}:{port}')
	# ルートの表示
	try:
		while True:
			client_socket, client_address = server_socket.accept()

			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, client_address),
				daemon=True
			)
			client_thread.start()
	except KeyboardInterrupt:
		logging.info('Server closing')
	finally:
		server_socket.close()
		logging.info('Server closed')

if __name__ == '__main__':
	run_server()
