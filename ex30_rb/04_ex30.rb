#!/usr/bin/env ruby

require 'json'

class MboxParser
  attr_reader :sender, :count

  def initialize(file_path)
    @file_path = file_path
    @sender = Hash.new(0)
    @count = 0
  end

  def parse()
    File.open(@file_path, "r") do |f|
      f.each_line do |line|
        if line.start_with?("From: ")
          matched = line.match(/[A-Z0-9.\-]+@[A-Z0-9.\-]+/i)
          @sender[matched[0]] += 1 if matched
        end
      end
    end
  end

  def count_sender()
    @count = @sender.values.sum
  end

end

def main()
  unless 1 <= ARGV.length
    puts "Usage: ./[This file] [.mbox] [option]"
    puts "Usage: if you want to puts result, use --read of -r option"
    return -1
  end

  file_path = ARGV[0]
  unless File.exist?(file_path)
    puts "ERROR: File is not exist"
    puts "File Path: #{file_path}"
    return -1
  end

  option = ""
  if ARGV.length == 2
    option = ARGV[1]
  end

  mbox_obj = MboxParser.new(file_path)
  mbox_obj.parse
  mbox_obj.count_sender

  json_str = JSON.pretty_generate(mbox_obj.sender)
  File.write("04_ex30.json", json_str)

  if option == "--read" or option == "-r"
    json_str = File.read("04_ex30.json")
    output = JSON.parse(json_str)

    output.each do |key, value|
      puts "#{key}: #{value}"
    end
  end

  return 0
end

if __FILE__ == $0
  main
end
