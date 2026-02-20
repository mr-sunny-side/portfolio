import logging
import mailbox
from email.header import decode_header
from email.utils import parseaddr
from collections import defaultdict
from email.utils import parsedate_to_datetime

"""
	02-20:	結果の表示テストから

"""

domain_dict = {}

def	set_log():
	logging.basicConfig(
		level=logging.DEBUG,
		format='%(levelname)s - %(message)s'
	)

class	DomainData:
	def	__init__(self):
		self.count		= 0
		self.subject	= defaultdict(int)	# 初期値が自動で0になる
		self.first_date	= None
		self.last_date	= None

	def	add_date(self, date_obj):
		# 始めてdate_objを受け取った場合、それを保存
		if self.first_date is None and self.last_date is None:
			self.first_date = date_obj
			self.last_date = date_obj

		# 最短、最長の日付の更新
		if date_obj < self.first_date:
			self.first_date = date_obj
		elif self.last_date < date_obj:
			self.last_date = date_obj

def	parse_domain(addr: str) -> str:
	try:
		domain = addr.split('@')[1].strip()
		return domain
	except IndexError:
		logging.exception('parse_domain/mbox.py: IndexError')

def	safe_decode(raw_subject: str) -> str:
	parts = decode_header(raw_subject)

	decoded_subs = []
	for content, encoding in parts:
		if isinstance(content, bytes):	# contentがbyte列ならエンコード
			charset = encoding or 'utf-8'
			sub = content.decode(charset, errors='replace')
			decoded_subs.append(sub)
		else:							# そうでなければそのまま保存
			decoded_subs.append(content)

	return ''.join(decoded_subs)

# date行が壊れているときのために関数で処理
def	parse_datetime(raw_date: str) -> object | None:
	if not raw_date:
		return None

	try:
		return parsedate_to_datetime(raw_date)
	except Exception:
		logging.exception("parse_datetime/mbox.py: cannot parse datetime line")
		return None

def	mbox_main(mail_data):
	set_log()
	mbox = mailbox.mbox(mail_data)

	for mail in mbox:
		# domainをパース
		addr = parseaddr(mail['from'])
		if not addr:
			logging.error('mbox_main/mbox.py: cannot parse address')
			logging.error(f'from line: {mail['from']}')
			continue
		domain = parse_domain(addr)

		# domain_dictに存在するか確認
		if domain not in domain_dict:
			domain_dict[domain] = DomainData()
		domain_data = domain_dict[domain]	# 辞書・リスト・objは一時変数の変更も共有される

		# domainの受信回数を記録
		domain_data.count += 1

		# subjectのデコード
		sub = safe_decode(mail['subject'])
		domain_data.subject[sub] += 1

		# datetime_objの作成・保存
		date_obj = parse_datetime(mail['date'])
		if date_obj is None:
			continue
		domain_data.add_date(date_obj)

# 最も頻繁な受信があったドメイン 3つ
# 最も多かった件名 3つ
# 最も長い期間受信していたドメインと日数 3つ
