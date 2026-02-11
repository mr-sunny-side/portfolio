#!/usr/bin/env ruby

TARGET = ['From: ', 'To: ']

unless ARGV.length == 1
  puts "Usage: ./[This file] [.mbox]"
  exit -1
end

file_path = ARGV[0]
unless File.exist?(file_path)
  puts "ERROR: file is not exist"
  puts "File Path: #{file_path}"
  exit -1
end

# メールアドレス抽出関数
def parse_address()
  # 自作関数の書き方
  # 正規表現による抽出方法

File.open(file_path, "r") do |file|
  file.each_line do |line|
    next unless TARGET.any?(|h| line.start_with?(h))

    parts = line.split(':', 2)
    header = parts[0]
    detail = parts[1]

    # parse_address関数
