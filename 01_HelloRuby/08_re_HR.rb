#!/usr/bin/env ruby

TARGET = [
  "From: ",
  "To: ",
  "Date: ",
  "Subject: "
]

header_count = 0
max_len = 0
max_value = ""

unless ARGV.length == 1
  puts "Usage: ./[This file] [.mbox]"
  exit -1
end

file_path = ARGV[0]
unless File.exist?(file_path)
  puts "ERROR: File not exist"
  puts "File Path: #{file_path}"
  exit -1
end

File.open(file_path, "r") do |file|
  file.each_line do |line|
    matched = TARGET.find{|h| line.start_with?(h)}
    next unless matched

    header_count += 1
    parts = line.split(':', 2)
    label = parts[0].strip
    detail = parts[1].strip

    length = detail.length
    if max_len < length
      max_len = length
      max_value = detail
    end

    puts "Header: #{label}"
    puts "Value: #{detail}"
    puts "---"
  end
end

puts "Total headers: #{header_count}"
puts "Longest value: #{max_value} (#{max_len} chars)"
