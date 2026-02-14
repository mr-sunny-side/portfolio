#!/usr/bin/env ruby

require 'nkf'
require 'logger'

LOG = logger.new(STDERR)
LOG.level = logger::INFO
LOG.formatter = proc do |severity, datetime, progname, msg|
  "[#{severity}]: #{msg}\n"
end

def make_pattern(filter_arg)
  filter_list = filter_arg.split(',').map(&:strip)

  patterns = []
  begin
    filter_list.each do |filter|
      safe_filter = Regexp.escape(filter)
      patterns << Regexp.new(safe_filter, Regexp::IGNORECASE)
  rescue RegexpError => e
    LOG.error("make_pattern: RegexpError")
    LOG.error(e.full_message)
  end

  pattern
end


def main()
  unless 1 <= ARGV.length
    LOG.error("main: Argument Error")
    exit -1
  end

  mbox = ARGV[0]
  unless File.exist?(mbox)
    LOG.error("main: File is not exist")
    exit -1
  end

  sender_fil = nil
  filter_idx = ARGV.index("-f")
  if filter_idx && ARGV[filter_idx + 1]
    # make_pattern
