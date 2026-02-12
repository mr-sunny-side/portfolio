#!/usr/bin/env ruby

class MboxParser
	attr_reader :sender, :emails_count		# 属性を外から読めるようにする

	def initialize(file_path)
		@file_path = file_path
		@emails_count = 0
		@sender = Hash.new(0)
	end

	def parse()
		File.open(@file_path, "r") do |f|
			f.each_line do |line|
				if line.start_with?("From: ")
					from_value = line.split(':', 2)[1].strip

					matched = from_value.match(/[A-Z0-9.\-]+@[A-Z0-9.\-]+/i)
					@sender[matched[0]] += 1 if matched
				end
			end
		end
	end

	def	count_emails()
		@emails_count = @sender.values.sum	# 値の合計を出す
	end
end

def	main()
	unless ARGV.length == 1
		puts "Usage: ./[This file] [.mbox]"
		exit -1
	end

	file_path = ARGV[0]
	unless File.exist?(file_path)
		puts "ERROR: File is not exist"
		exit -1
	end

	mbox_obj = MboxParser.new(file_path)	# コンストラクタは.newで呼ぶ
	mbox_obj.parse()
	mbox_obj.count_emails()

	mbox_obj.sender.each do |key, value|
		puts "#{key}: #{value}"
	end

	puts "---"
	puts "Total emails #{mbox_obj.emails_count}"
end

if __FILE__ == $0
	main
end
