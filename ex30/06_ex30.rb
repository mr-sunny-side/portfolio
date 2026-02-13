#!/usr/bin/env ruby

"""
  02-13: main関数でメソッドチェーンの実装から

"""

require 'logger'
require 'nkf'

logger = Logger.new(STDERR)
logger.level = Logger::DEBUG

# アドレスと件名をセットにしたリストを作成
def mbox_parser(file_path)
  target = ["From ", "From: ", "Subject: "]
  email_list = []             # emailの情報を格納するリスト
  sender_dict = {}            # emailの情報の単位

  File.open(file_path, "r") do |f|
    f.each_line do |line|
      next unless target.any?{|h| line.start_with?(h)}

      # From行なら前のsender情報を保存・新しくdictを作成
      if line.start_with?("From ")
        if !sender_dict.empty?
          email_list << sender_dict
        end
        sender_dict = {}
      end

      # 予め情報を分割して保存
      value = line.split(':', 2)[1].strip

      if line.start_with?("From: ")
        matched = value.match(/[a-z0-9.\-]+@[a-z0-9.\-]+/i)
        sender_dict[:from] = matched ? matched[0] : "unknown"
      elsif line.start_with?("Subject: ")
        decoded = NKF.nkf('-w', value)
        sender_dict[:subject] = decoded
      end
    end

    if !sender_dict.empty?
      email_list << sender_dict
    end
  end

  email_list
end

def make_pattern(raw_filter)
  filter_list = raw_filter.split(',').map(&:strip)

  pattern = []
  begin
    filter_list.each do |filter|
      safe_filter = Regexp.escape(filter)                   # まずエスケープ
      pattern << Regexp.new(safe_filter, Regexp::IGNORECASE)# コンパイルして保存
  rescue RegexpError => e
    logger.error("make_pattern: Invalid filter")
    logger.error(e.full_message)
  end

  pattern
end

def main()
  unless 2 <= ARGV.length
    logger.error("Usage: ./[This file] [.mbox] [filter option]")
    logger.error("filter Option: filtering address. You can input multiple addresses to ','")
    exit -1
  end

  file_path = ARGV[0]
  unless File.exist?(file_path)
    logger.error("File is not exist")
    exit -1
  end

  # フィルター条件をコンパイル・リストに保存
  filter_raw = ARGV[1]
  if ARGV.length == 2
    pattern = make_pattern(filter_raw)
  end

  emails_list = mbox_parser(file_path)
  logger.info("Extract #{email_list.size} addresses")

  # メソッドチェーンを実装
  if pattern
    filtered_list = emails_list.select do |email|   # selectでemails_listからemailを取り出す
      pattern.any?{|p| p.match(email[:from])}       # emailがpatternとマッチするか検証
    end
  end
  logger.info("Filtered to #{filtered list.size} addresses")

  uniq_list = filter_list.uniq.sort
  logger.info("Removed duplicate, #{uniq_list.size} unique addresses")
  logger.info("Sorted alphabetically")

  logger.info("Result:")
  uniq_list.each{|sender| logger.info(sender)}
end

if __FILE__ == $0
  main()
end
