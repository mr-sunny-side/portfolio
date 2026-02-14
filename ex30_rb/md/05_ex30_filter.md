# 05_ex30.rb のフィルター機能の問題点解説

## 該当コード（77-88行目）

```ruby
# オプションの実装
sender_fil = nil
sender_idx = ARGV.index('--filter')
if sender_idx && ARGV[sender_idx + 1]
  sender_fil = ARGV[sender_idx + 1]
end

# sender_listを事前にフィルター
sender_list = mbox_parser(file_path)
filtered = sender_list
if sender_fil
  filtered = sender_list.select{|email| email['From'] == sender_fil}
end
```

## 主な問題点

### 1. **完全一致による厳格なフィルタリング**

87行目で `email['From'] == sender_fil` という**完全一致**の比較を行っています。

```ruby
filtered = sender_list.select{|email| email['From'] == sender_fil}
```

**問題:**
- 大文字・小文字の違いがあるとマッチしない
- 余分なスペースがあるとマッチしない
- 部分一致での検索ができない

**例:**
```ruby
# メール内のアドレス: "user@example.com"
# フィルター指定: "User@Example.com"
# 結果: マッチしない（大文字小文字が異なる）

# メール内のアドレス: "user@example.com"
# フィルター指定: "example.com"
# 結果: マッチしない（部分一致は不可）
```

### 2. **デバッグ情報の欠如**

フィルター処理が実行されているかどうか、何件マッチしたかなどの情報が出力されないため、問題の切り分けが困難です。

### 3. **エラーハンドリングの不足**

- フィルター条件に一致するメールが0件の場合でもエラーメッセージが出ない
- ユーザーは「フィルターが動いていないのか」「該当メールがないのか」判断できない

## 改善案

### 改善案1: 大文字小文字を無視した部分一致

```ruby
# sender_listを事前にフィルター
sender_list = mbox_parser(file_path)
filtered = sender_list
if sender_fil
  # 大文字小文字を無視して部分一致
  filtered = sender_list.select do |email|
    email['From'].downcase.include?(sender_fil.downcase)
  end

  # フィルター結果を表示
  puts "Filter: '#{sender_fil}' -> #{filtered.length} emails found"
end
```

### 改善案2: デバッグ情報の追加

```ruby
# sender_listを事前にフィルター
sender_list = mbox_parser(file_path)
puts "Total emails parsed: #{sender_list.length}"

filtered = sender_list
if sender_fil
  puts "Applying filter: '#{sender_fil}'"
  filtered = sender_list.select{|email| email['From'] == sender_fil}
  puts "Matched emails: #{filtered.length}"

  if filtered.empty?
    puts "WARNING: No emails matched the filter"
    puts "Available addresses:"
    sender_list.map{|e| e['From']}.uniq.sort.each{|addr| puts "  - #{addr}"}
  end
end
```

### 改善案3: 正規表現によるフレキシブルなマッチング

```ruby
if sender_fil
  begin
    # 正規表現としてマッチング（大文字小文字を無視）
    pattern = Regexp.new(sender_fil, Regexp::IGNORECASE)
    filtered = sender_list.select{|email| email['From'] =~ pattern}
    puts "Filter pattern: /#{sender_fil}/i -> #{filtered.length} emails found"
  rescue RegexpError => e
    puts "ERROR: Invalid filter pattern: #{e.message}"
    return -1
  end
end
```

## 推奨される完全な実装

```ruby
# オプションの実装
sender_fil = nil
sender_idx = ARGV.index('--filter')
if sender_idx && ARGV[sender_idx + 1]
  sender_fil = ARGV[sender_idx + 1]
end

# sender_listを事前にフィルター
sender_list = mbox_parser(file_path)
puts "Total emails: #{sender_list.length}"

filtered = sender_list
if sender_fil
  puts "Filtering by: '#{sender_fil}'"

  # 大文字小文字を無視した部分一致
  filtered = sender_list.select do |email|
    email['From']&.downcase&.include?(sender_fil.downcase)
  end

  puts "Matched: #{filtered.length} emails"

  if filtered.empty?
    puts "\nNo emails matched the filter."
    puts "Available sender addresses:"
    sender_list.map{|e| e['From']}.compact.uniq.sort.each do |addr|
      puts "  - #{addr}"
    end
  end
end

puts "\n--- Filtered Results ---\n" if sender_fil && !filtered.empty?
```

## まとめ

現在のコードの主な問題は:
1. **完全一致のみ**で柔軟性がない
2. **大文字小文字を区別**してしまう
3. **デバッグ情報がない**ため問題の特定が困難

これらを改善することで、より使いやすく、問題の切り分けがしやすいフィルター機能になります。

---

# Rubyの基礎文法解説（初心者向け）

## 1. begin-rescue-end文（例外処理）

`begin-rescue-end`はPythonの`try-except-finally`に相当する、例外処理のための構文です。

### 基本構文

```ruby
begin
  # 実行したいコード（例外が発生する可能性がある）
rescue ExceptionType => variable
  # 例外が発生した時の処理
ensure
  # 必ず実行される処理（Pythonのfinally相当）
end
```

### 具体例

```ruby
# 例1: 基本的な使い方
begin
  result = 10 / 0  # ZeroDivisionErrorが発生
rescue ZeroDivisionError => e
  puts "エラー: ゼロ除算が発生しました"
  puts "詳細: #{e.message}"
end

# 例2: 複数の例外を処理
begin
  pattern = Regexp.new("[invalid")  # RegexpErrorが発生
  file = File.open("nonexistent.txt")  # Errno::ENOENTが発生
rescue RegexpError => e
  puts "正規表現エラー: #{e.message}"
rescue Errno::ENOENT => e
  puts "ファイルが見つかりません: #{e.message}"
rescue => e  # すべての例外をキャッチ
  puts "予期しないエラー: #{e.class} - #{e.message}"
end

# 例3: ensure節を使う
begin
  file = File.open("data.txt", "r")
  data = file.read
rescue Errno::ENOENT => e
  puts "ファイルエラー: #{e.message}"
ensure
  file.close if file  # 例外の有無に関わらず必ず実行される
  puts "処理を終了します"
end
```

### フィルター機能での使用例

```ruby
if sender_fil
  begin
    # 正規表現のコンパイルを試みる
    pattern = Regexp.new(sender_fil, Regexp::IGNORECASE)
    filtered = sender_list.select{|email| email['From'] =~ pattern}
    puts "Filter pattern: /#{sender_fil}/i -> #{filtered.length} emails found"
  rescue RegexpError => e
    # 正規表現が不正な場合のエラー処理
    puts "ERROR: Invalid filter pattern: #{e.message}"
    puts "Example: Use 'example\\.com' to match literal dots"
    return -1
  end
end
```

### Pythonとの比較

```python
# Python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"エラー: {e}")
finally:
    print("終了")
```

```ruby
# Ruby
begin
  result = 10 / 0
rescue ZeroDivisionError => e
  puts "エラー: #{e}"
ensure
  puts "終了"
end
```

## 2. 正規表現（Regular Expression）

Rubyには正規表現を扱う複数の方法があります。

### 正規表現リテラル

```ruby
# リテラル表記（最も一般的）
pattern = /example\.com/i
# /pattern/フラグ の形式
# フラグ:
#   i = 大文字小文字を無視（ignore case）
#   m = マルチラインモード
#   x = 拡張モード（スペースとコメントを無視）

# 使用例
email = "user@example.com"
if email =~ /example\.com/i  # =~ はマッチ演算子
  puts "マッチしました"
end
```

### Regexp.new による生成

```ruby
# 動的にパターンを作成する場合
user_input = "example.com"
pattern = Regexp.new(user_input, Regexp::IGNORECASE)

# フラグの種類
# Regexp::IGNORECASE または Regexp::IGNORECASE  # 大文字小文字を無視
# Regexp::MULTILINE   # 複数行モード
# Regexp::EXTENDED    # 拡張モード

# 複数のフラグを組み合わせ
pattern = Regexp.new(user_input, Regexp::IGNORECASE | Regexp::MULTILINE)
```

### マッチング方法

```ruby
text = "user@example.com"
pattern = /example\.com/

# 方法1: =~ 演算子（マッチした位置を返す、マッチしない場合はnil）
if text =~ pattern
  puts "マッチしました（位置: #{text =~ pattern}）"
end

# 方法2: match メソッド（MatchDataオブジェクトを返す）
match_data = text.match(pattern)
if match_data
  puts "マッチした文字列: #{match_data[0]}"
end

# 方法3: === 演算子（case文で便利）
case text
when /example\.com/
  puts "example.comが含まれています"
when /test\.org/
  puts "test.orgが含まれています"
end
```

### 特殊文字のエスケープ

```ruby
# 特殊文字: . * + ? [ ] ( ) { } ^ $ | \
# これらをリテラルとして扱うには \ でエスケープ

# ドットをリテラルとして扱う
pattern1 = /example.com/     # 「example」+「任意の1文字」+「com」
pattern2 = /example\.com/    # 「example.com」（ドットがリテラル）

# Regexp.newの場合、バックスラッシュを2重にする
pattern3 = Regexp.new("example\\.com")  # "example.com"にマッチ
```

### フィルター機能での実用例

```ruby
# 例1: ドメイン名でフィルタリング
domain = "example.com"
pattern = Regexp.new(Regexp.escape(domain), Regexp::IGNORECASE)
# Regexp.escapeで特殊文字を自動エスケープ

filtered = sender_list.select do |email|
  email['From'] =~ pattern
end

# 例2: より柔軟なパターン
# "gmail.com" または "googlemail.com" のアドレスを抽出
pattern = /(gmail|googlemail)\.com/i
filtered = sender_list.select{|email| email['From'] =~ pattern}

# 例3: ユーザー入力を安全に処理
user_input = params[:filter]  # ユーザーからの入力
safe_pattern = Regexp.escape(user_input)  # 特殊文字をエスケープ
pattern = Regexp.new(safe_pattern, Regexp::IGNORECASE)
```

## 3. Rubyのロギング（Logging）

Rubyには標準ライブラリの`Logger`があり、Pythonの`logging`モジュールに相当します。

### 基本的な使い方

```ruby
require 'logger'

# ロガーの作成
logger = Logger.new(STDOUT)  # 標準出力に出力
# または
logger = Logger.new('logfile.log')  # ファイルに出力
# または
logger = Logger.new(STDERR)  # 標準エラー出力に出力

# ログレベルの設定
logger.level = Logger::DEBUG  # すべてのログを出力
# ログレベル: DEBUG < INFO < WARN < ERROR < FATAL < UNKNOWN

# ログの出力
logger.debug("デバッグ情報")
logger.info("情報メッセージ")
logger.warn("警告メッセージ")
logger.error("エラーメッセージ")
logger.fatal("致命的エラー")
```

### フィルター機能でのロガー使用例

```ruby
#!/usr/bin/env ruby

require 'nkf'
require 'time'
require 'json'
require 'logger'

# グローバルロガーの設定
$logger = Logger.new(STDERR)  # 標準エラー出力に出力
$logger.level = Logger::INFO   # INFOレベル以上を出力

# デバッグモードの追加
if ARGV.include?('--debug')
  $logger.level = Logger::DEBUG
  ARGV.delete('--debug')
end

def mbox_parser(file_path)
  $logger.info("Parsing mbox file: #{file_path}")

  target = ["From: ", "Date: ", "Subject: "]
  sender_list = []
  cur_data = nil

  File.open(file_path, "r") do |f|
    line_count = 0
    f.each_line do |line|
      line_count += 1

      if line.start_with?("From ")
        if cur_data && !cur_data.empty?
          sender_list << cur_data
          $logger.debug("Email #{sender_list.length} parsed")
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
          $logger.warn("Invalid date format at line #{line_count}: #{e.message}")
          cur_data['Date'] = value  # 文字列のまま保存
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

def main()
  unless 1 <= ARGV.length
    puts "Usage: ./[This file] [.mbox] [option]"
    puts "Option: --filter [pattern]: filter by sender address (regex)"
    puts "        --debug: enable debug logging"
    return -1
  end

  file_path = ARGV[0]
  unless File.exist?(file_path)
    $logger.error("File does not exist: #{file_path}")
    puts "ERROR: File is not exist"
    puts "File Path: #{file_path}"
    return -1
  end

  # filterオプションの実装
  sender_fil = nil
  sender_idx = ARGV.index('--filter')
  if sender_idx && ARGV[sender_idx + 1]
    sender_fil = ARGV[sender_idx + 1]
    $logger.info("Filter pattern specified: '#{sender_fil}'")
  end

  # sender_listを事前にフィルター
  sender_list = mbox_parser(file_path)
  filtered = sender_list

  if sender_fil
    begin
      # 正規表現としてマッチング（大文字小文字を無視）
      safe_pattern = Regexp.escape(sender_fil)  # 特殊文字をエスケープ
      pattern = Regexp.new(safe_pattern, Regexp::IGNORECASE)

      $logger.debug("Applying regex filter: /#{safe_pattern}/i")
      filtered = sender_list.select{|email| email['From'] =~ pattern}

      $logger.info("Filtered results: #{filtered.length} / #{sender_list.length} emails")

      if filtered.empty?
        $logger.warn("No emails matched the filter pattern")
        puts "\nNo emails matched the filter: '#{sender_fil}'"
        puts "\nAvailable sender addresses:"
        sender_list.map{|e| e['From']}.compact.uniq.sort.each do |addr|
          puts "  - #{addr}"
        end
        return 0
      end

    rescue RegexpError => e
      $logger.error("Invalid regex pattern: #{e.message}")
      puts "ERROR: Invalid filter pattern: #{e.message}"
      puts "Pattern: '#{sender_fil}'"
      return -1
    end
  end

  $logger.debug("Outputting filtered results")
  filtered.each do |sender_data|
    puts "---"
    sender_data.each do |key, value|
      puts "#{key}: #{value}"
    end
  end

  return 0
end
```

### ログレベルの詳細

```ruby
# DEBUG: 詳細なデバッグ情報（開発時のみ）
logger.debug("変数の値: x=#{x}, y=#{y}")

# INFO: 一般的な情報メッセージ
logger.info("処理を開始しました")

# WARN: 警告（処理は継続するが注意が必要）
logger.warn("設定ファイルが見つかりません。デフォルト値を使用します")

# ERROR: エラー（処理に失敗したが、プログラムは継続）
logger.error("データの保存に失敗しました")

# FATAL: 致命的エラー（プログラムの継続が困難）
logger.fatal("データベース接続に失敗しました")
```

### カスタムフォーマット

```ruby
logger = Logger.new(STDOUT)

# フォーマットのカスタマイズ
logger.formatter = proc do |severity, datetime, progname, msg|
  "[#{datetime.strftime('%Y-%m-%d %H:%M:%S')}] #{severity}: #{msg}\n"
end

logger.info("これはカスタムフォーマットです")
# 出力: [2024-02-12 14:30:45] INFO: これはカスタムフォーマットです
```

### 簡易的なロギング（Loggerを使わない場合）

```ruby
# 環境変数でデバッグモードを制御
DEBUG = ENV['DEBUG'] == 'true' || ARGV.include?('--debug')

def log_debug(message)
  puts "[DEBUG] #{message}" if DEBUG
end

def log_info(message)
  puts "[INFO] #{message}"
end

def log_error(message)
  $stderr.puts "[ERROR] #{message}"  # 標準エラー出力
end

def log_warn(message)
  $stderr.puts "[WARN] #{message}"
end

# 使用例
log_info("処理を開始します")
log_debug("変数の値: #{var}")
log_error("ファイルが見つかりません")
```

### Pythonとの比較

```python
# Python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.debug("デバッグ")
logger.info("情報")
logger.warning("警告")
logger.error("エラー")
logger.critical("致命的")
```

```ruby
# Ruby
require 'logger'

logger = Logger.new(STDOUT)
logger.level = Logger::INFO

logger.debug("デバッグ")
logger.info("情報")
logger.warn("警告")
logger.error("エラー")
logger.fatal("致命的")
```

## 実装のベストプラクティス

### 1. デバッグモードの実装

```ruby
# コマンドライン引数で制御
DEBUG = ARGV.include?('--debug')
ARGV.delete('--debug') if DEBUG

$logger = Logger.new(STDERR)
$logger.level = DEBUG ? Logger::DEBUG : Logger::INFO

# 使い方: ./script.rb file.mbox --debug
```

### 2. 環境変数での制御

```ruby
# 環境変数 DEBUG=1 で制御
DEBUG = ENV['DEBUG'] == '1' || ENV['DEBUG'] == 'true'

$logger = Logger.new(STDERR)
$logger.level = DEBUG ? Logger::DEBUG : Logger::WARN

# 使い方: DEBUG=1 ./script.rb file.mbox
```

### 3. 詳細度レベル（Verbosity）

```ruby
# -v, -vv, -vvv で詳細度を制御
verbosity = ARGV.count{|arg| arg == '-v'}
ARGV.delete_if{|arg| arg == '-v'}

$logger = Logger.new(STDERR)
case verbosity
when 0
  $logger.level = Logger::WARN   # 警告以上のみ
when 1
  $logger.level = Logger::INFO   # 情報以上
when 2
  $logger.level = Logger::DEBUG  # デバッグ含む全て
else
  $logger.level = Logger::DEBUG
end

# 使い方:
# ./script.rb file.mbox        # WARN以上
# ./script.rb file.mbox -v     # INFO以上
# ./script.rb file.mbox -vv    # DEBUG含む全て
```
