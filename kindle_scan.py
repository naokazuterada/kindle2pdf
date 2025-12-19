import pyautogui
import time
import os

# --- 設定項目 ---
SAVE_DIR = "kindle_screenshots"  # 保存フォルダ名
TOTAL_PAGES = 100                # 取りたいページ数
INTERVAL = 1.5                   # ページめくりの待機時間（通信環境に合わせて調整）
NEXT_PAGE_KEY = 'left'          # キーボードの右矢印でめくる場合
# ----------------

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print("5秒後に開始します。Kindleを最前面に表示してください。")
time.sleep(5)

for i in range(TOTAL_PAGES):
    # ファイル名を 001.png のような形式にする
    file_name = f"{i+1:03d}.png"
    file_path = os.path.join(SAVE_DIR, file_name)

    # スクリーンショットを撮って保存
    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)

    # ページをめくる（キー入力 または click(x, y)）
    pyautogui.press(NEXT_PAGE_KEY)

    print(f"{file_name} を保存しました")
    time.sleep(INTERVAL)

print("完了しました！")
