#!/usr/bin/env ruby

unless ARGV.length == 1
  puts "Usage: ./[This file] [Text file]"
  exit -1
end

file_path = ARGV[0]
unless File.exist?(file_path)
  puts "ERROR: File is not exist"
  puts "file_path: #{file_path}"
  exit -1
end

line_count = 0
File.open(file_path, 'r') do |file|
  file.each_line do |line|
    line_count += 1
    puts "#{line_count}: #{line}"
  end
  puts "---"
  puts "Total lines: #{line_count}"
end
