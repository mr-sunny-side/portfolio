#!/usr/bin/env ruby

TARGET = ['From: ', 'To: ']
header_count = 0

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
def ext_address(line)
  # 正規表現による抽出方法
  matched = line.match(/[A-Z0-9.\-]+@[A-Z0-9.\-]+/i)
  return nil unless matched

  matched[0]
end

File.open(file_path, "r") do |file|
  file.each_line do |line|
    next unless TARGET.any?{|h| line.start_with?(h)}

    parts = line.split(':', 2)
    header = parts[0].strip
    detail = parts[1].strip
    # parse_address関数
    address = ext_address(detail)
    unless address
      puts "Warning: Cannot extract address"
      puts "Line: #{line}"
      next
    end

    header_count += 1
    domain = address.split('@')[1]
    puts "#{header} Domain: #{domain}"
  end
end

puts "Total address: #{header_count}"
