import logging
from urllib.parse import urlparse, parse_qs

import config

config.setting_logging()

class Request:
	def	__init__(self):
		self.method: str = None
		self.path: str = None
		self.version: str = None
		self.type: str  = None
		self.length: int = None
		self.query = {}
		self.body = {}

def	get_request(client_socket, request_obj: Request) -> int:
	# ヘッダー終了まで読み込み
	buffer = b''
	while b'\r\n\r\n' in buffer:
		buffer += client_socket.recv(config.BUFFER_SIZE)
		if buffer == b'':		# バッファが空なら終了
			logging.warning('get_request: Request is empty', exc_info=True)
			return -1
		if config.MAX_READ < len(buffer):
			logging.error('get_request: Request header is too big')
			logging.error(f'get_request: buffer len={len(buffer)}')
			return -1
	logging.debug('get_request: found header end')

	# ヘッダーとボディを分割
	header_end = buffer.find(b'\r\n\r\n')
	header_part = buffer[:header_end]
	body_part = buffer[header_end + 4:]
	logging.debug('get_request: got raw header data')

	# ヘッダーをパースするためにデコード
	header_part = header_part.decode('utf-8', errors='replace')
	logging.debug('get_request: decoded header data')

	# httpリクエストをパース・保存
	header_lines = header_part.split('\r\n')
	# parse_http関数呼び出し
