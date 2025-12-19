import pyautogui
import time
import os
from io import BytesIO

# --- 設定項目 ---
SAVE_DIR = "output/screenshots"  # 保存フォルダ名
MAX_PAGES = 1000                 # 最大ページ数（安全のための上限）
INTERVAL = 1                     # ページめくりの待機時間（通信環境に合わせて調整）
NEXT_PAGE_KEY = 'left'           # キーボードの左矢印でめくる場合
DUPLICATE_THRESHOLD = 5          # 同じ画面が何回続いたら停止するか
# ----------------

def get_image_bytes(image):
    """画像をバイト列に変換して比較用に返す"""
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print("5秒後に開始します。Kindleを最前面に表示してください。")
time.sleep(5)

last_image_bytes = None
duplicate_count = 0
saved_count = 0
duplicates_to_remove = []

for i in range(MAX_PAGES):
    # スクリーンショットを撮る
    screenshot = pyautogui.screenshot()
    current_image_bytes = get_image_bytes(screenshot)

    # ファイル名を 001.png のような形式にする
    file_name = f"{i+1:03d}.png"
    file_path = os.path.join(SAVE_DIR, file_name)

    # 前回と同じ画像かチェック
    if last_image_bytes == current_image_bytes:
        duplicate_count += 1
        print(f"{file_name} は前回と同じ画像です（{duplicate_count}/{DUPLICATE_THRESHOLD}）")

        # 重複画像も一旦保存（後で削除するためリストに追加）
        screenshot.save(file_path)
        duplicates_to_remove.append(file_path)

        if duplicate_count >= DUPLICATE_THRESHOLD:
            print(f"\n{DUPLICATE_THRESHOLD}回連続で同じ画像が続いたため、終了します。")
            break
    else:
        # 新しい画像の場合
        duplicate_count = 0
        duplicates_to_remove = []  # 重複リストをリセット
        screenshot.save(file_path)
        saved_count += 1
        print(f"{file_name} を保存しました（{saved_count}ページ目）")

    last_image_bytes = current_image_bytes

    # ページをめくる（キー入力 または click(x, y)）
    pyautogui.press(NEXT_PAGE_KEY)
    time.sleep(INTERVAL)

# 重複した画像を削除（最初の1枚は残す）
for dup_path in duplicates_to_remove:
    if os.path.exists(dup_path):
        os.remove(dup_path)
        print(f"重複画像を削除: {os.path.basename(dup_path)}")

print(f"\n完了しました！ 合計 {saved_count} ページを保存しました。")
