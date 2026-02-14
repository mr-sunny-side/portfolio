# 08_HelloRuby.rb コードレビュー

## 📝 概要
mboxファイルからメールヘッダー（From, To, Subject）を読み取り、最長の値を見つけるプログラム

---

## ✅ 良い点

### 1. エラーハンドリング
```ruby
unless ARGV.length == 1
  puts "Usage: ./[This file] [.mbox]"
  exit -1
end

unless File.exist?(file_path)
  puts "ERROR: File is not exist"
  exit -1
end
```
- コマンドライン引数のチェック
- ファイル存在確認
- 適切なエラーメッセージ

### 2. ブロックを使ったファイル処理
```ruby
File.open(file_path, "r") do |file|
  # ...
end
```
- ブロック終了時に自動的にファイルがクローズされる
- Rubyらしい書き方

### 3. 文字列メソッドの活用
```ruby
line.start_with?("From: ")
parts[1].strip
```
- `start_with?` で前方一致判定
- `strip` で空白除去

---

## ⚠️ 改善点

### 1. **重大な問題：コードの重複（DRY原則違反）**

現在のコード：
```ruby
if line.start_with?("From: ")
  header_count += 1
  parts = line.split(':')
  length = parts[1].strip.length
  if max_len < length
    max_len = length
    max_value = parts[1].strip
  end
  puts "Header: #{parts[0].strip}"
  puts "Value: #{parts[1].strip}"
  puts "---"
elsif line.start_with?("To: ")
  # 全く同じコードが繰り返される...
elsif line.start_with?("Subject: ")
  # またまた同じコードが...
end
```

**問題点：**
- 同じロジックが3回繰り返されている
- 新しいヘッダーを追加する場合、また同じコードをコピペする必要がある
- 修正が必要な場合、3箇所すべてを変更しなければならない

**改善案：**
```ruby
# ヘッダー名を配列で定義
headers = ["From:", "To:", "Subject:"]

File.open(file_path, "r") do |file|
  file.each_line do |line|
    # いずれかのヘッダーで始まるかチェック
    header = headers.find { |h| line.start_with?(h) }

    if header
      header_count += 1
      parts = line.split(':', 2)  # ← 注意：2を指定
      value = parts[1].strip
      length = value.length

      if length > max_len
        max_len = length
        max_value = value
      end

      puts "Header: #{parts[0].strip}"
      puts "Value: #{value}"
      puts "---"
    end
  end
end
```

### 2. **`split(':')`の問題**

現在のコード：
```ruby
parts = line.split(':')
```

**問題点：**
- メールアドレスやURLに`:`が含まれる場合に誤動作
- 例：`From: user@example.com (sent at 10:30:45)` → 3つに分割されてしまう

**改善案：**
```ruby
parts = line.split(':', 2)  # 最大2つに分割
```

### 3. **変数名が不明確**

```ruby
max_value = ""
max_len = 0
```

**問題点：**
- どのヘッダーの最長値かわからない
- 複数のヘッダー種別がある場合に混乱

**改善案：**
```ruby
longest_header_value = ""
longest_value_length = 0
```

### 4. **マジックナンバー/マジックストリング**

```ruby
if line.start_with?("From: ")
elsif line.start_with?("To: ")
```

**改善案：**
```ruby
# ファイル冒頭で定義
TARGET_HEADERS = ["From:", "To:", "Subject:"]
```

---

## 🎯 リファクタリング後の完全版

```ruby
#!/usr/bin/env ruby

# コマンドライン引数チェック
unless ARGV.length == 1
  puts "Usage: ./[This file] [.mbox]"
  exit -1
end

file_path = ARGV[0]
unless File.exist?(file_path)
  puts "ERROR: File does not exist"
  exit -1
end

# 対象ヘッダーを配列で定義
TARGET_HEADERS = ["From:", "To:", "Subject:"].freeze

header_count = 0
longest_value = ""
longest_length = 0

File.open(file_path, "r") do |file|
  file.each_line do |line|
    # いずれかのヘッダーで始まるかチェック
    matched_header = TARGET_HEADERS.find { |h| line.start_with?(h) }

    next unless matched_header  # マッチしなければスキップ

    header_count += 1

    # ヘッダー名と値に分割（最大2分割）
    parts = line.split(':', 2)
    header_name = parts[0].strip
    header_value = parts[1].strip

    # 最長値を更新
    if header_value.length > longest_length
      longest_length = header_value.length
      longest_value = header_value
    end

    # 結果表示
    puts "Header: #{header_name}"
    puts "Value: #{header_value}"
    puts "---"
  end
end

puts "Total headers: #{header_count}"
puts "Longest value: #{longest_value} (#{longest_length} chars)"
```

---

## 📚 学習ポイント

### 1. **DRY原則（Don't Repeat Yourself）**
- 同じコードを繰り返さない
- 共通部分を抽出してメソッドや配列で管理

### 2. **配列とイテレータの活用**
```ruby
# ❌ 悪い例
if line.start_with?("From:")
elsif line.start_with?("To:")
elsif line.start_with?("Subject:")

# ✅ 良い例
headers.find { |h| line.start_with?(h) }
```

### 3. **`split`の第2引数**
```ruby
line.split(':', 2)  # 最大2つに分割
```

### 4. **`next`を使った早期リターン**
```ruby
next unless condition  # 条件に合わなければスキップ
```

### 5. **定数の使用**
```ruby
TARGET_HEADERS = ["From:", "To:", "Subject:"].freeze
```
- `.freeze`で変更不可にする
- マジックストリングを避ける

---

## 🚀 さらなる改善案

### 1. ヘッダーごとの統計を取る
```ruby
header_stats = Hash.new(0)

# ヘッダーごとにカウント
header_stats[header_name] += 1
```

### 2. メソッドに分割
```ruby
def process_header(line)
  parts = line.split(':', 2)
  {
    name: parts[0].strip,
    value: parts[1].strip
  }
end
```

### 3. 正規表現を使う
```ruby
if line =~ /^(From|To|Subject):\s*(.+)$/
  header_name = $1
  header_value = $2
end
```

---

## 💡 まとめ

**現在のスキル：**
- ✅ ファイル処理の基本
- ✅ 文字列操作
- ✅ 条件分岐

**次のステップ：**
- 🎯 DRY原則の実践
- 🎯 配列・ハッシュの活用
- 🎯 イテレータとブロックの使いこなし
- 🎯 コードの抽象化

**総合評価：** ⭐⭐⭐☆☆ (3/5)
- 基本的な機能は動作する
- ただし、コードの重複が多く、保守性が低い
- リファクタリングを学ぶ良い機会！
