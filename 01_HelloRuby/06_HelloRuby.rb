#!/usr/bin/env ruby

5.times do |num|
  puts num + 1
end

puts "---"

fruits = ["apple", "banana", "cherry"]
fruits.each do |fruit|
  puts "I like #{fruit} (#{fruit.length} characters)"
end
