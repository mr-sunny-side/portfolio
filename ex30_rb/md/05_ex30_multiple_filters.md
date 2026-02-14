# 複数フィルターの実装方法

## 1. `params` vs `ARGV` の違い

### Webアプリケーション（Rails/Sinatra）
```ruby
# Webアプリケーションでの例
# URL: /emails?filter=example.com&filter=test.org
filters = params[:filter]  # ["example.com", "test.org"]
```

### コマンドラインツール（今回のケース）
```ruby
# コマンドライン引数を使用
# 実行: ./script.rb file.mbox --filter example.com --filter test.org
ARGV  # => ["file.mbox", "--filter", "example.com", "--filter", "test.org"]
```

## 2. 複数フィルターの実装パターン

### パターン1: 複数の`--filter`オプション（OR条件）

いずれかのパターンにマッチするメールを抽出

```ruby
# 実行例: ./05_ex30.rb file.mbox --filter gmail.com --filter yahoo.com

def main()
  unless 1 <= ARGV.length
    puts "Usage: ./[This file] [.mbox] [option]"
    puts "Option: --filter [pattern]: filter by sender address (can be specified multiple times)"
    puts "        Multiple filters are combined with OR logic"
    return -1
  end

  file_path = ARGV[0]
  unless File.exist?(file_path)
    puts "ERROR: File is not exist"
    return -1
  end

  # 複数のfilterオプションを収集
  sender_filters = []
  ARGV.each_with_index do |arg, idx|
    if arg == '--filter' && ARGV[idx + 1]
      sender_filters << ARGV[idx + 1]
    end
  end

  # sender_listを取得
  sender_list = mbox_parser(file_path)
  filtered = sender_list

  # 複数フィルターの適用（OR条件）
  if sender_filters.any?
    puts "Filters: #{sender_filters.inspect}"

    # 各フィルターパターンをコンパイル
    patterns = []
    sender_filters.each do |filter_str|
      begin
        safe_pattern = Regexp.escape(filter_str)
        patterns << Regexp.new(safe_pattern, Regexp::IGNORECASE)
      rescue RegexpError => e
        puts "ERROR: Invalid filter pattern '#{filter_str}': #{e.message}"
        return -1
      end
    end

    # いずれかのパターンにマッチするものを抽出（OR条件）
    filtered = sender_list.select do |email|
      patterns.any? { |pattern| email['From'] =~ pattern }
    end

    puts "Matched: #{filtered.length} / #{sender_list.length} emails"
  end

  # 結果の出力
  filtered.each do |sender_data|
    puts "---"
    sender_data.each { |key, value| puts "#{key}: #{value}" }
  end

  return 0
end
```

### パターン2: カンマ区切りで複数指定（シンプル）

```ruby
# 実行例: ./05_ex30.rb file.mbox --filter "gmail.com,yahoo.com,outlook.com"

def main()
  file_path = ARGV[0]
  unless File.exist?(file_path)
    puts "ERROR: File is not exist"
    return -1
  end

  # filterオプションの実装
  sender_fil = nil
  sender_idx = ARGV.index('--filter')
  if sender_idx && ARGV[sender_idx + 1]
    sender_fil = ARGV[sender_idx + 1]
  end

  sender_list = mbox_parser(file_path)
  filtered = sender_list

  if sender_fil
    # カンマ区切りで分割
    filter_patterns = sender_fil.split(',').map(&:strip)
    puts "Filters: #{filter_patterns.inspect}"

    # 各パターンをコンパイル
    patterns = []
    filter_patterns.each do |filter_str|
      begin
        safe_pattern = Regexp.escape(filter_str)
        patterns << Regexp.new(safe_pattern, Regexp::IGNORECASE)
      rescue RegexpError => e
        puts "ERROR: Invalid filter pattern '#{filter_str}': #{e.message}"
        return -1
      end
    end

    # OR条件でフィルタリング
    filtered = sender_list.select do |email|
      patterns.any? { |pattern| email['From'] =~ pattern }
    end

    puts "Matched: #{filtered.length} / #{sender_list.length} emails"
  end

  filtered.each do |sender_data|
    puts "---"
    sender_data.each { |key, value| puts "#{key}: #{value}" }
  end

  return 0
end
```

### パターン3: AND条件とOR条件の両方サポート

```ruby
# 実行例（OR条件）: ./05_ex30.rb file.mbox --filter-or gmail.com --filter-or yahoo.com
# 実行例（AND条件）: ./05_ex30.rb file.mbox --filter-and user --filter-and example.com

def main()
  file_path = ARGV[0]
  unless File.exist?(file_path)
    puts "ERROR: File is not exist"
    return -1
  end

  # OR条件のフィルター収集
  or_filters = []
  ARGV.each_with_index do |arg, idx|
    if arg == '--filter-or' && ARGV[idx + 1]
      or_filters << ARGV[idx + 1]
    end
  end

  # AND条件のフィルター収集
  and_filters = []
  ARGV.each_with_index do |arg, idx|
    if arg == '--filter-and' && ARGV[idx + 1]
      and_filters << ARGV[idx + 1]
    end
  end

  sender_list = mbox_parser(file_path)
  filtered = sender_list

  # OR条件の適用
  if or_filters.any?
    puts "OR Filters: #{or_filters.inspect}"
    or_patterns = or_filters.map do |f|
      Regexp.new(Regexp.escape(f), Regexp::IGNORECASE)
    end

    filtered = filtered.select do |email|
      or_patterns.any? { |pattern| email['From'] =~ pattern }
    end
    puts "After OR filter: #{filtered.length} emails"
  end

  # AND条件の適用
  if and_filters.any?
    puts "AND Filters: #{and_filters.inspect}"
    and_patterns = and_filters.map do |f|
      Regexp.new(Regexp.escape(f), Regexp::IGNORECASE)
    end

    filtered = filtered.select do |email|
      and_patterns.all? { |pattern| email['From'] =~ pattern }
    end
    puts "After AND filter: #{filtered.length} emails"
  end

  filtered.each do |sender_data|
    puts "---"
    sender_data.each { |key, value| puts "#{key}: #{value}" }
  end

  return 0
end
```

## 3. 推奨実装（パターン1の改良版）

実用的で柔軟な実装例:

```ruby
#!/usr/bin/env ruby

require 'nkf'
require 'time'
require 'json'
require 'logger'

# グローバルロガーの設定
$logger = Logger.new(STDERR)
$logger.level = Logger::INFO

# デバッグモードの追加
if ARGV.include?('--debug')
  $logger.level = Logger::DEBUG
  ARGV.delete('--debug')
end

def parse_from(from_value)
  matched = from_value.match(/[A-Z0-9.\-]+@[A-Z0-9.\-]+/i)
  matched ? matched[0] : nil
end

def mbox_parser(file_path)
  $logger.info("Parsing mbox file: #{file_path}")

  target = ["From: ", "Date: ", "Subject: "]
  sender_list = []
  cur_data = nil

  File.open(file_path, "r") do |f|
    f.each_line do |line|
      if line.start_with?("From ")
        if cur_data && !cur_data.empty?
          sender_list << cur_data
        end
        cur_data = {}
        next
      end

      next unless target.any?{|h| line.start_with?(h)}
      value = line.split(':', 2)[1].strip

      if line.start_with?("From: ")
        address = parse_from(value)
        cur_data['From'] = address ? address : "unknown"
      elsif line.start_with?("Date: ")
        begin
          date_obj = Time.parse(value)
          cur_data['Date'] = date_obj
        rescue ArgumentError => e
          $logger.warn("Invalid date format: #{e.message}")
          cur_data['Date'] = value
        end
      elsif line.start_with?("Subject: ")
        decoded_sub = NKF.nkf("-w", value)
        cur_data['Subject'] = decoded_sub
      end
    end
  end

  if cur_data && !cur_data.empty?
    sender_list << cur_data
  end

  $logger.info("Total emails parsed: #{sender_list.length}")
  sender_list.sort_by {|mail| mail['Date']}
end

def collect_filter_options(argv, option_name)
  """複数の同じオプションを収集する"""
  filters = []
  argv.each_with_index do |arg, idx|
    if arg == option_name && argv[idx + 1] && !argv[idx + 1].start_with?('--')
      filters << argv[idx + 1]
    end
  end
  filters
end

def compile_patterns(filter_strings)
  """フィルター文字列を正規表現パターンにコンパイル"""
  patterns = []
  filter_strings.each do |filter_str|
    begin
      # 特殊文字をエスケープして安全に
      safe_pattern = Regexp.escape(filter_str)
      patterns << Regexp.new(safe_pattern, Regexp::IGNORECASE)
      $logger.debug("Compiled pattern: /#{safe_pattern}/i")
    rescue RegexpError => e
      $logger.error("Invalid filter pattern '#{filter_str}': #{e.message}")
      raise
    end
  end
  patterns
end

def apply_filters(sender_list, patterns, logic: :or)
  """
  複数のパターンでフィルタリング
  logic: :or => いずれかにマッチ、:and => すべてにマッチ
  """
  case logic
  when :or
    sender_list.select do |email|
      patterns.any? { |pattern| email['From'] =~ pattern }
    end
  when :and
    sender_list.select do |email|
      patterns.all? { |pattern| email['From'] =~ pattern }
    end
  else
    raise ArgumentError, "logic must be :or or :and"
  end
end

def main()
  unless 1 <= ARGV.length
    puts "Usage: ./[This file] [.mbox] [options]"
    puts "Options:"
    puts "  --filter [pattern]     : Filter by sender address (can be specified multiple times)"
    puts "                           Multiple filters are combined with OR logic"
    puts "  --filter-and [pattern] : AND logic filter (all patterns must match)"
    puts "  --debug                : Enable debug logging"
    puts ""
    puts "Examples:"
    puts "  ./05_ex30.rb file.mbox --filter gmail.com --filter yahoo.com"
    puts "  ./05_ex30.rb file.mbox --filter-and user --filter-and example.com"
    return -1
  end

  file_path = ARGV[0]
  unless File.exist?(file_path)
    $logger.error("File does not exist: #{file_path}")
    puts "ERROR: File is not exist"
    puts "File Path: #{file_path}"
    return -1
  end

  # フィルターオプションの収集
  or_filters = collect_filter_options(ARGV, '--filter')
  and_filters = collect_filter_options(ARGV, '--filter-and')

  if or_filters.any?
    $logger.info("OR Filters: #{or_filters.inspect}")
  end
  if and_filters.any?
    $logger.info("AND Filters: #{and_filters.inspect}")
  end

  # メールパース
  sender_list = mbox_parser(file_path)
  filtered = sender_list

  # OR条件フィルターの適用
  if or_filters.any?
    begin
      patterns = compile_patterns(or_filters)
      filtered = apply_filters(filtered, patterns, logic: :or)
      $logger.info("After OR filter: #{filtered.length} / #{sender_list.length} emails")
    rescue RegexpError
      return -1
    end
  end

  # AND条件フィルターの適用
  if and_filters.any?
    begin
      patterns = compile_patterns(and_filters)
      filtered = apply_filters(filtered, patterns, logic: :and)
      $logger.info("After AND filter: #{filtered.length} / #{sender_list.length} emails")
    rescue RegexpError
      return -1
    end
  end

  # 結果が空の場合
  if (or_filters.any? || and_filters.any?) && filtered.empty?
    $logger.warn("No emails matched the filter patterns")
    puts "\nNo emails matched the filters."
    puts "\nAvailable sender addresses:"
    sender_list.map{|e| e['From']}.compact.uniq.sort.each do |addr|
      puts "  - #{addr}"
    end
    return 0
  end

  # 結果の出力
  $logger.debug("Outputting #{filtered.length} filtered results")
  filtered.each do |sender_data|
    puts "---"
    sender_data.each do |key, value|
      puts "#{key}: #{value}"
    end
  end

  return 0
end

if __FILE__ == $0
  main()
end
```

## 4. 実行例

```bash
# OR条件: gmail.com または yahoo.com のいずれか
./05_ex30.rb file.mbox --filter gmail.com --filter yahoo.com

# AND条件: "user" かつ "example.com" の両方を含む
./05_ex30.rb file.mbox --filter-and user --filter-and example.com

# 組み合わせ: (gmail.com OR yahoo.com) AND user
./05_ex30.rb file.mbox --filter gmail.com --filter yahoo.com --filter-and user

# デバッグモード付き
./05_ex30.rb file.mbox --filter gmail.com --debug
```

## 5. まとめ

あなたの理解は正しいです：

1. ✅ **パラメータとして受け取り**: `ARGV`から複数の`--filter`オプションを収集
2. ✅ **エスケープしてコンパイル**: `Regexp.escape`で安全に、`Regexp.new`でコンパイル
3. ✅ **パターン群でフィルター**: `select`と`any?`/`all?`を使って効率的にフィルタリング

実装の流れ:
```
コマンドライン引数
  ↓
フィルター文字列の収集
  ↓
正規表現パターンにコンパイル
  ↓
OR/AND条件でフィルタリング
  ↓
結果の出力
```
