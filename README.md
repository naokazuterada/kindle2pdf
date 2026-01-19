# Kindle書籍 自動スクショ・プロジェクト

Kindle書籍を自動でスクリーンショット撮影し、NotebookLMに読み込ませるためのワークフローです。

作成時のやりとり
https://gemini.google.com/app/2d79c34f2b3802f7?hl=ja

## フォルダ構成

- `venv/` : Python仮想環境（システムを汚さず実行するための環境）
- `1_kindle_scan.py` : 自動撮影を実行するメインスクリプト
- `2_create_pdf.py` : 画像をPDFに変換し、必要に応じて32MB以下に分割するスクリプト
- `0_check_pos.py` : マウスの座標を確認するためのスクリプト（通常は不要）
- `output/` : 出力フォルダ（実行時に自動生成）
  - `screenshots/` : 撮影された画像が保存される
  - `books/` : PDFファイルの保存先
    - `book.pdf` : 生成されたPDFファイル
    - `book/` : 分割されたPDFファイル（32MB超の場合に自動生成）
      - `0001.pdf`, `0002.pdf`, ... : 分割後のPDFファイル

## 事前準備（macOS設定）

pyautoguiが画面操作を行うために、以下の許可が必要です。

1. **システム設定** > **プライバシーとセキュリティ** > **アクセシビリティ** を開く
2. **ターミナル**（または使用しているエディタ）を ON にする

### 実行前の注意事項

- **Kindleは最初のページを開いておく**: スクリプト実行前に、撮影を開始したいページを表示しておいてください
- **外部ディスプレイは外す**: 複数ディスプレイ環境では座標がずれる可能性があるため、外部ディスプレイを外した状態で実行してください
- **ページ送り方向を確認**: `1_kindle_scan.py` の `NEXT_PAGE_KEY` を本に合わせて設定してください
  - `'left'` : 横書きの本（← でページが進む）
  - `'right'` : 縦書きの本（→ でページが進む）

## 環境構築（初回のみ）

### 1. 仮想環境を作成する

```bash
python3 -m venv venv
```

### 2. 仮想環境を有効にする

```bash
source venv/bin/activate
```

> ターミナルの先頭に `(venv)` と表示されれば成功です。

### 3. 必要なパッケージをインストールする

```bash
pip install pyautogui Pillow pypdf
```

## 使い方（手順）

### 1. 仮想環境を有効にする

ターミナルを開くたびに、このコマンドを実行して環境をアクティベートしてください。

```bash
source venv/bin/activate
```

> ターミナルの先頭に `(venv)` と表示されれば成功です。

### 2. 自動スクショを実行する

```bash
python3 1_kindle_scan.py
```

- 実行後、5秒以内にKindleアプリを最前面に表示し、最初のページを開きます
- 設定したページ数分、自動で「撮影 → めくり」が繰り返されます

### 3. 仮想環境を終了する

作業が終わったら、以下のコマンドで環境を抜けます。

```bash
deactivate
```

## PDF化とNotebookLMへのアップロード

### PDFを作成する

```bash
python3 2_create_pdf.py
```

**処理内容:**
1. `output/screenshots/` 内の画像をファイル名順に結合して `output/books/book.pdf` を作成
2. ファイルサイズが32MBを超える場合、自動的に分割します
   - 分割ファイルは `output/books/book/0001.pdf`, `0002.pdf`, ... に保存されます
3. 32MB以下の場合は分割せず、そのまま完了します

### 既存のPDFを分割する

すでにPDFがあって、それを分割したい場合:

**単一ファイルの場合:**
```bash
python3 2_create_pdf.py path/to/your.pdf
```

**複数ファイルを一括処理する場合:**
```bash
python3 2_create_pdf.py file1.pdf file2.pdf file3.pdf
```

これで指定したPDFファイルを32MB以下に分割できます。複数指定した場合は順番に処理されます。

### NotebookLMへのアップロード

出来上がったPDFを [NotebookLM](https://notebooklm.google.com/) にアップロードします。

- **分割されなかった場合**: `output/books/book.pdf` をそのままアップロード
- **分割された場合**: `output/books/book/` フォルダ内の `0001.pdf`, `0002.pdf`, ... を順番にアップロード

> NotebookLMが自動で高精度なOCRを行うため、画像PDFのままで問題ありません。

## スクリプトの調整のコツ

| 問題 | 解決方法 |
|------|----------|
| ページがめくれない | `1_kindle_scan.py` の `pyautogui.press('left')` を `pyautogui.click(x, y)` に書き換える（座標は `python3 0_check_pos.py` で確認） |
| 画像が真っ白になる | KindleのDRM保護により標準のスクショが制限されている可能性あり。`INTERVAL`を長めにするか、フルスクリーンモードを解除する |
