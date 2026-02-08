import re

import config

routes = []

config.setting_logging()

class Response:
	def __init__(self, status=200, reason='OK', headers=None, body=''):
		self.status = status
		self.reason = reason
		self.headers = headers if headers else {}
		self.body = body

		if 'Connection' not in self.headers:
			self.headers['Connection'] = 'close'

	def to_bytes(self):
		response = f'HTTP/1.1 {self.status} {self.reason}\r\n'
		for label, detail in self.headers.items():
			response += f'{label}: {detail}\r\n'
		response += '\r\n'

		# bodyがすでにbytes型なのを加味して、先にheaderをエンコード
		response = response.encode('utf-8', errors='replace')

		if isinstance(self.body, bytes):
			response += self.body
		else:
			response += self.body.encode('utf-8', errors='replace')
		return response

# ルーティング関数
def	route(path):
	def	register(handler):
		pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
		pattern = f'^{pattern}$'
		routes.append((re.compile(pattern), handler))
		return handler
	return register
