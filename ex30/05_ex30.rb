#!/usr/bin/env ruby

"""
  02-12: フィルタリングの実装から

"""

require 'nkf'
require 'time'
require 'json'

def parse_from(from_value)
  matched = from_value.match(/[A-Z0-9.\-]+@[A-Z0-9.\-]+/i)
  matched ? matched[0] : nil
end

def mbox_parser(file_path)
  target = [
    "From: ",
    "Date: ",
    "Subject: "
  ]
  sender_list = []
  cur_data = nil

  File.open(file_path, "r") do |f|
    f.each_line do |line|

      # 先頭行だったらdictの存在を確認してlistに保存
      if line.start_with?("From ")
        if cur_data && !cur_data.empty?   # 要するにちゃんとあるか確認して追加することが重要
          sender_list << cur_data
        end
        cur_data = {}
        next
      end
      next unless target.any?{|h| line.start_with?(h)}

      value = line.split(':', 2)[1].strip

      # 各ヘッダーごとの処理・カレントハッシュに保存
      if line.start_with?("From: ")
        address = parse_from(value)
        cur_data['From'] = address ? address : "unknown"
      elsif line.start_with?("Date: ")
        date_obj = Time.parse(value)
        cur_data['Date'] = date_obj
      elsif line.start_with?("Subject: ")
        decoded_sub = NKF.nkf("-w", value)
        cur_data['Subject'] = decoded_sub
      end
    end
  end

  if cur_data && !cur_data.empty?
    sender_list << cur_data
  end

  sender_list = sender_list.sort_by {|mail| mail['Date']} # 最後に.reverseメソッドを呼べば降順にできる
end

def main()
  unless 1 <= ARGV.length
    puts "Usage: ./[This file] [.mbox] [option]"
    puts "Option: --filter: filter sender address"
    return -1
  end

  file_path = ARGV[0]
  unless File.exist?(file_path)
    puts "ERROR: File is not exist"
    puts "File Path: #{file_path}"
    return -1
  end

  # filterオプションの実装
  sender_fil = nil
  sender_idx = ARGV.index('--filter')
  if sender_idx && ARGV[sender_idx + 1]
    sender_fil = ARGV[sender_idx + 1]
  end

  # sender_listを事前にフィルター
  sender_list = mbox_parser(file_path)
  filtered = sender_list
  if sender_fil
    # filterはコンマで複数指定できるので、分割
    filter_pattern = sender_fil.split(',').map(&:strip)   # filter_pattern.map{|pattern| pattern.strip}の省略

    # 各フィルターをエスケープしてコンパイル
    patterns = []
    filter_pattern.each do |filter_str|
      begin
        safe_pattern = Regexp.escape(filter_str)          # フィルター内容をエスケープ
        patterns << Regexp.new(safe_pattern, Regexp::IGNORECASE)    # ケース不問でコンパイルして、patternリストに追加
      rescue RegexpError => e
        puts "ERROR: Invalid filter pattern #{filter_str}: #{e.message}"
        return -1
      end

      # 完成した条件でフィルター
      filtered = sender_list.select do |email|
        patterns.any?{|pattern| pattern =~ email['From']}
      end
    end

  end

  filtered.each do |sender_data|
    puts "---"
    sender_data.each {|key, value| puts "#{key}: #{value}"}
  end

  return 0
end

if __FILE__ == $0
  main()
end
