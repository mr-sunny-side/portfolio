import re
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
		self.boundary: str = None
		self.query = {}
		self.body = {}

def	parse_http(http_line, request_obj: Request) -> bool:
	parts = http_line.split()
	if len(parts) != 3:
		return False

	request_obj.method = parts[0]
	request_obj.version = parts[2]

	url = urlparse(parts[1])
	request_obj.path = url.path
	request_obj.query = parse_qs(url.query)
	return True

def	get_boundary(request_obj: Request) -> bool:
	# multipart~とboundaryを分割
	parts = request_obj.type.split()
	if len(parts) != 2:
		return False

	request_obj.type = parts[0].rstrip('\r\n')
	boundary_part = parts[1]

	boundary_start = boundary_part.find('boundary=')
	request_obj.boundary = boundary_part[boundary_start + len('boundary='):]
	logging.debug(f'get_boundary: type={request_obj.type}')
	logging.debug(f'get_boundary: boundary={request_obj.boundary}')
	return True


def	get_type_length(header_lines, request_obj: Request) -> bool:
	for header in header_lines:
		# content-typeを保存
		if header.startswith('Content-Type:'):
			request_obj.type = header.split(':')[1].lstrip().rstrip('\r\n')
			# boundaryがある場合、boundaryを保存
			if 'multipart/form-data;' in request_obj.type:
				return False if not get_boundary(request_obj) else True
		# content-lengthを保存
		if header.startswith('Content-Length:'):
			request_obj.length = int(header.split(':')[1].lstrip().rstrip('\r\n'))

	if request_obj.type is None or request_obj.length is None:
		logging.debug('get_type_length: Cannot found type or length')
		return False
	return True

def	get_form_data(body_part: bytes, request_obj: Request):
	boundary_bytes = request_obj.boundary.encode('utf-8', errors='replace')		# boundaryをエンコード
	parts = body_part.split(boundary_bytes)								# エンコードしたboundaryで分割
	for form in parts[1:]:												# 最初は'--'なので飛ばす
		if form == b'--':												# また'--'が来たら終了
			break
		form_parts = form.split(b'\r\n\r\n')							# form本体とdescriptionを分割
		form_parts[0] = form_parts[0].decode('utf-8', errors='replace') # 正規表現を使うためにname=の行だけデコード

		matched = re.search(r'name="(\w+)"', form_parts[0])				# descriptionからnameを捕捉
		if matched:
			name = matched.group(1)										# request.bodyに保存。keyはname=をデコードしたもの
			request_obj.body[name] = form_parts[1].rstrip(b'\r\n')					# データ本体は\r\nをstrip()して保存

def	get_request(client_socket, request_obj: Request) -> bool:
	# ヘッダー終了まで読み込み
	buffer = b''
	while not b'\r\n\r\n' in buffer:
		buffer += client_socket.recv(config.BUFFER_SIZE)
		if buffer == b'':		# バッファが空なら終了
			logging.warning('get_request: request is empty')
			return False
		if config.MAX_READ < len(buffer):
			logging.error('get_request: request header is too big')
			logging.error(f'get_request: buffer len={len(buffer)}')
			return False
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
	if not parse_http(header_lines[0], request_obj):
		logging.error('parse_http/get_request: returned error')
		return False

	# GETメソッドならここで終了
	if request_obj.method == 'GET':
		logging.debug('get_request: request method is GET')
		return True

	# content-type, lengthを取得
	if not get_type_length(header_lines[1:], request_obj):
		logging.debug('get_type_length/get_request: returned error')
		return False

	# 残りのbodyを取得
	body_part += client_socket.recv(request_obj.length - len(body_part))
	logging.debug('get_request: got latest body_part')

	# type == application/x-www-form-urlencodedならbodyをパースして保存
	if request_obj.type == 'application/x-www-form-urlencoded':
		body_part = body_part.decode('utf-8', errors='replace')
		request_obj.body = parse_qs(body_part)
		return True

	# type == ファイル送信ならget_form_data関数を呼び出し
	if request_obj.type == 'multipart/form-data;':
		get_form_data(body_part, request_obj)
	return True

def	print_request(request_obj):
	logging.info('===== Request =====')
	logging.info(f'{"method":<15}:{request_obj.method}')
	logging.info(f'{"path":<15}:{request_obj.path}')
	logging.info(f'{"version":<15}:{request_obj.version}')
	logging.info(f'{"type":<15}:{request_obj.type}')
	if request_obj.boundary:
		logging.info(f'{"boundary":<15}:{request_obj.boundary}')
	logging.info(f'{"query":<15}:')
	for label, detail in request_obj.query.items():
		detail = ','.join(detail)
		logging.info(f'\t{label:<15}:{detail}')
	logging.info(f'{"body":<15}:')
	for label, detail in request_obj.body.items():
		if isinstance(detail, bytes):
			logging.info(f'\t{label:<15}:{len(detail)}')
		else:
			detail = ','.join(detail)
			logging.info(f'\t{label:<15}:{detail}')
