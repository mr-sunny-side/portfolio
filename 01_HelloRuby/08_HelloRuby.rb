#!/usr/bin/env ruby

unless ARGV.length == 1
  puts "Usage: ./[This file] [.mbox]"
  exit -1
end

file_path = ARGV[0]
unless File.exist?(file_path)
  puts "ERROR: File is not exist"
  exit -1
end

header_count = 0
max_value = ""
max_len = 0
File.open(file_path, "r") do |file|
  file.each_line do |line|
    if line.start_with?("From: ")
      header_count += 1
      parts = line.split(':')
      length = parts[1].strip.length
      if max_len < length
        max_len = length
        max_value = parts[1].strip
      end

      puts "Header: #{parts[0].strip}"
      puts "Value: #{parts[1].strip}"
      puts "---"
    elsif line.start_with?("To: ")
      header_count += 1
      parts = line.split(':')
      length = parts[1].strip.length
      if max_len < length
        max_len = length
        max_value = parts[1].strip
      end

      puts "Header: #{parts[0].strip}"
      puts "Value: #{parts[1].strip}"
      puts "---"
    elsif line.start_with?("Subject: ")
      header_count += 1
      parts = line.split(':')
      length = parts[1].strip.length
      if max_len < length
        max_len = length
        max_value = parts[1].strip
      end

      puts "Header: #{parts[0].strip}"
      puts "Value: #{parts[1].strip}"
      puts "---"
    end
  end
end

puts "Total headers: #{header_count}"
puts "Longest value: #{max_value} (#{max_len} chars)"
