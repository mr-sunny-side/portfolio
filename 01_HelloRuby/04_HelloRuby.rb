#!/usr/bin/env ruby

unless 1 == ARGV.length
  puts "ERROR: Please provide a number"
  exit -1
end

unless ARGV[0].respond_to?(:to_i)
  puts "ERROR: Please provide a number"
  exit -1
end

if ARGV[0].to_i < 10
  puts "Small number"
elsif ARGV[0].to_i == 10
  puts "Just right"
elsif 10 < ARGV[0].to_i
  puts "Big number"
end
