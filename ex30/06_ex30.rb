#!/usr/bin/env ruby

require 'logger'

logger = Logger.new(STDERR)
logger.level = Logger::DEBUG

def main()
  unless 1 <= ARGV.length
