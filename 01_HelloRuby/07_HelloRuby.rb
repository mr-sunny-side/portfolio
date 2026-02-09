#!/usr/bin/env ruby

unless ARGV.length == 3
  puts "Usage: ./[This file] [Name] [Age] [Language]"
  exit -1
end

person = {
  "name": ARGV[0],
  "age": ARGV[1],
  "lang": ARGV[2]
}

person.each do |key, value|
  puts "#{key}: #{value}"
end
puts "---"

puts "My name is #{person[:name]}"
