#!/usr/bin/env ruby

if ARGV.length < 1
	puts "Usage: [This file] [argument]"
	exit 1
end

name = ARGV[0]
puts "Hello, #{name} !"
