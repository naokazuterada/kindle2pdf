import pyautogui
import time
import os
import sys
import tty
import termios

# --- 設定項目 ---
SAVE_DIR = "output/screenshots"  # 保存フォルダ名
MAX_PAGES = 1000                 # 最大ページ数（安全のための上限）
INTERVAL = 1                     # ページめくりの待機時間（通信環境に合わせて調整）
DUPLICATE_THRESHOLD = 3          # 同じ画面が何回続いたら停止するか
TOOLBAR_HEIGHT_RETINA = 104      # 削除するメニューバーの高さ（Retinaディスプレイ用）
# ----------------

def get_display_scale():
    """ディスプレイのスケールファクターを取得（Retinaなら2、通常なら1）"""
    screen_width, _ = pyautogui.size()  # 論理解像度
    screenshot = pyautogui.screenshot()
    actual_width = screenshot.size[0]   # 実際のピクセル数
    return actual_width // screen_width

def read_arrow_key():
    """矢印キーを読み取る（左右のみ対応）"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # エスケープシーケンス
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 == 'D':  # 左矢印
                    return 'left'
                elif ch3 == 'C':  # 右矢印
                    return 'right'
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def select_page_direction():
    """ページ送り方向を選択"""
    print("ページ送り方向を選択してください（矢印キーで選択）:")
    print("  ← : 左方向 - 日本語の縦書き・マンガなど")
    print("  → : 右方向 - 横書きの本など")

    while True:
        direction = read_arrow_key()
        if direction:
            print(f"  → {direction} を選択しました")
            return direction

def select_crop_toolbar():
    """ツールバー削除オプションを選択（デフォルトは削除する）"""
    print("画面上部のツールバーを削除しますか？")
    choice = input("  [Y]/n (Enterで削除): ").strip().lower()
    return choice != 'n'

DISPLAY_SCALE = get_display_scale()
TOOLBAR_HEIGHT = TOOLBAR_HEIGHT_RETINA if DISPLAY_SCALE >= 2 else TOOLBAR_HEIGHT_RETINA // 2

NEXT_PAGE_KEY = select_page_direction()
CROP_TOOLBAR = select_crop_toolbar()

def get_pixel_data_for_comparison(image):
    """比較用のピクセルデータを取得（メニューバーの時刻変化を除外するため上部をクロップ）"""
    width, height = image.size
    # 上部50ピクセルを除外（メニューバーの時刻が変わっても影響しないように）
    cropped = image.crop((0, 50, width, height))
    return cropped.tobytes()

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print("5秒後に開始します。Kindleを最前面に表示してください。")
time.sleep(5)

last_pixel_data = None
duplicate_count = 0
saved_count = 0
duplicates_to_remove = []

for i in range(MAX_PAGES):
    # スクリーンショットを撮る
    screenshot = pyautogui.screenshot()
    current_pixel_data = get_pixel_data_for_comparison(screenshot)

    # ファイル名を 001.png のような形式にする
    file_name = f"{i+1:03d}.png"
    file_path = os.path.join(SAVE_DIR, file_name)

    # 前回と同じ画像かチェック（ピクセルデータで比較）
    if last_pixel_data == current_pixel_data:
        duplicate_count += 1
        print(f"{file_name} は前回と同じ画像です（{duplicate_count}/{DUPLICATE_THRESHOLD}）")

        # 重複画像も一旦保存（後で削除するためリストに追加）
        image_to_save = screenshot
        if CROP_TOOLBAR:
            width, height = screenshot.size
            image_to_save = screenshot.crop((0, TOOLBAR_HEIGHT, width, height))
        image_to_save.save(file_path)
        duplicates_to_remove.append(file_path)

        if duplicate_count >= DUPLICATE_THRESHOLD:
            print(f"\n{DUPLICATE_THRESHOLD}回連続で同じ画像が続いたため、終了します。")
            break
    else:
        # 新しい画像の場合
        duplicate_count = 0
        duplicates_to_remove = []  # 重複リストをリセット
        image_to_save = screenshot
        if CROP_TOOLBAR:
            width, height = screenshot.size
            image_to_save = screenshot.crop((0, TOOLBAR_HEIGHT, width, height))
        image_to_save.save(file_path)
        saved_count += 1
        print(f"{file_name} を保存しました（{saved_count}ページ目）")

    last_pixel_data = current_pixel_data

    # ページをめくる（キー入力 または click(x, y)）
    pyautogui.press(NEXT_PAGE_KEY)
    time.sleep(INTERVAL)

# 重複した画像を削除（最初の1枚は残す）
for dup_path in duplicates_to_remove:
    if os.path.exists(dup_path):
        os.remove(dup_path)
        print(f"重複画像を削除: {os.path.basename(dup_path)}")

print(f"\n完了しました！ 合計 {saved_count} ページを保存しました。")
