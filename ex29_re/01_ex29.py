#!/usr/bin/env python3

"""
	02-14:	handle_clientの記述から
			- とりあえずリクエスト情報を全部取得するところまで

"""


import logging
import socket
import threading
import config

config.set_log()

def	handle_client(client_socket, client_address):
	pass

def	main():
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((config.LOCAL, config.PORT))
	server_socket.listen(5)
	logging.info("main: Server listening")
	logging.info(f"{config.LOCAL}:{config.PORT}")
	# ルートの表示

	try:
		while True:
			client_socket, client_address = server_socket.accept()

			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, client_address)
				daemon=True
			)
			client_thread.start()
	except KeyboardInterrupt:
		logging.info("Server closing")
	finally:
		server_socket.close()
		logging.info("Server closed")
