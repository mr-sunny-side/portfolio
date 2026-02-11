#!/usr/bin/env ruby

TARGET = [
  'From ',
  'From: ',
  'To: ',
  'Subject: '
]

domain_dict = Hash.new(0)   # これで辞書が作成できる
mail_count = 0

unless ARGV.length == 1
  puts "Usage: ./[This file] [.mbox]"
  exit -1
end

file_path = ARGV[0]
unless File.exist?(file_path)
  puts "ERROR: File is not exist"
  puts "File Path: #{file_path}"
  exit -1
end

def ext_address(line)
  matched = line.match(/[A-Z0-9.\-]+@[A-Z0-9.\-]+/i)
  return nil unless matched

  matched[0]
end

File.open(file_path, "r") do |file|
  file.each_line do |line|
    next unless TARGET.any?{|h| line.start_with?(h)}

    if line.start_with?('From ')
      mail_count += 1
      puts "---"
      puts "Email: #{mail_count}"
      next
    end

    parts = line.split(':', 2)
    header = parts[0].strip
    detail = parts[1].to_s.strip    # 内容が空の場合、nilを文字列変換して防御
    puts "\t#{header}: #{detail}"

    if line.start_with?('From: ')
      address = ext_address(detail)
      next unless address           # アドレスが抽出できない場合スキップ
      domain = address.split('@')[1]
      domain_dict[domain] += 1
    end
  end
end

puts "---"
puts "Total Emails: #{mail_count}"
puts "Domain statistics:"
domain_dict.each do |domain, count|
  puts "\t#{domain}: #{count}"
end
