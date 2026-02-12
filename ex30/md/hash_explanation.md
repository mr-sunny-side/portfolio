# 05_ex30.rb の問題解説

## 1. まず「ハッシュ」とは？

ハッシュは、**キーと値のペアを保存する入れ物**です。

### 例：
```ruby
person = {
  "name" => "太郎",
  "age" => 25,
  "email" => "taro@example.com"
}
```

これは1つのハッシュで、1人分の情報を保存しています。

- キー `"name"` の値は `"太郎"`
- キー `"age"` の値は `25`
- キー `"email"` の値は `"taro@example.com"`

---

## 2. 元のコードの問題

### 元のコードが何も表示されなかった理由

**問題：ファイルの最後に `main()` の呼び出しがない**

```ruby
def main()
  # ... コード ...
  return 0
end

# ← ここに main() がない！
```

関数を定義しただけで、実行していませんでした。

**修正：ファイルの最後に `main()` を追加**

```ruby
def main()
  # ... コード ...
  return 0
end

main()  # ← これを追加
```

---

## 3. 現在のコードの動作（もう1つの問題）

### コードが何をしているか

```ruby
def mbox_parser(file_path)
  sender_list = []  # 空の配列

  File.open(file_path, "r") do |f|
    f.each_line do |line|
      # From:, Date:, Subject: で始まる行だけ処理
      next unless target.any?{|h| line.start_with?(h)}

      cur_data = {}  # ← 毎回、新しい空のハッシュを作る
      value = line.split(':', 2)[1].strip

      if line.start_with?("From: ")
        cur_data['From'] = address
      elsif line.start_with?("Date: ")
        cur_data['Date'] = date_obj
      elsif line.start_with?("Subject: ")
        cur_data['Subject'] = decoded_sub
      end

      sender_list << cur_data  # ← ハッシュを配列に追加
    end
  end

  sender_list  # ← 配列を返す
end
```

### 実際の動作

メールファイルに以下のような内容があるとします：

```
...
Subject: こんにちは
...
Date: Wed, 8 Oct 2025 13:46:42 +0000
From: taro@example.com
...
```

**コードの処理：**

1. `Subject:` の行を見つける
   - 新しい `cur_data = {}` を作る
   - `cur_data['Subject'] = "こんにちは"` を保存
   - `sender_list` に追加 → `[{"Subject"=>"こんにちは"}]`

2. `Date:` の行を見つける
   - **また新しい** `cur_data = {}` を作る
   - `cur_data['Date'] = ...` を保存
   - `sender_list` に追加 → `[{"Subject"=>"こんにちは"}, {"Date"=>...}]`

3. `From:` の行を見つける
   - **また新しい** `cur_data = {}` を作る
   - `cur_data['From'] = "taro@example.com"` を保存
   - `sender_list` に追加 → `[{"Subject"=>"こんにちは"}, {"Date"=>...}, {"From"=>"taro@example.com"}]`

### 結果

**3つの別々のハッシュ**ができます：

```ruby
[
  {"Subject" => "こんにちは"},
  {"Date" => 2025-10-08 13:46:42 +0000},
  {"From" => "taro@example.com"}
]
```

### 出力

```
---
Subject: こんにちは
---
Date: 2025-10-08 13:46:42 +0000
---
From: taro@example.com
```

各ハッシュごとに `---` で区切られて表示されます。

---

## 4. 望ましい動作（もし1通のメールを1つにまとめたいなら）

### 理想的な結果

1つのメールの情報を**1つのハッシュ**にまとめる：

```ruby
[
  {
    "From" => "taro@example.com",
    "Date" => 2025-10-08 13:46:42 +0000,
    "Subject" => "こんにちは"
  }
]
```

### 理想的な出力

```
---
From: taro@example.com
Date: 2025-10-08 13:46:42 +0000
Subject: こんにちは
```

1つのメールが1つのブロックで表示されます。

---

## 5. まとめ

### 現在の状態

- ✅ `main()` を追加したので、コードは実行されるようになった
- ❌ しかし、各ヘッダー行（From, Date, Subject）が別々のハッシュになっている

### 現在のコードの動作

- **1つのメールが3つのハッシュに分かれて表示される**

### もし変更が必要なら

1つのメールを1つのハッシュにまとめるには、ロジックの変更が必要です。
（メールの境界を判定して、同じメールのヘッダーを1つのハッシュに集める必要があります）
