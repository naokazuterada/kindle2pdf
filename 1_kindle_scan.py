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
# ----------------

def toggle_fullscreen():
    """フルスクリーンをトグルする（macOS: Control+Command+F）"""
    pyautogui.keyDown('ctrl')
    pyautogui.keyDown('command')
    pyautogui.press('f')
    pyautogui.keyUp('command')
    pyautogui.keyUp('ctrl')
    time.sleep(1)  # フルスクリーン切り替えアニメーションを待つ

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

NEXT_PAGE_KEY = select_page_direction()

def get_pixel_data_for_comparison(image):
    """比較用のピクセルデータを取得"""
    return image.tobytes()

def remove_black_bar(image):
    """画像上部の黒い帯を自動検出して削除"""
    width, height = image.size
    pixels = image.load()

    # 上部から黒い行を検出
    black_threshold = 30  # この値以下のRGB値を黒とみなす
    black_row_end = 0

    for y in range(height):
        # 行の左端から一定範囲のピクセルをチェック（全幅チェックは重いので）
        is_black_row = True
        check_points = [int(width * 0.1), int(width * 0.3), int(width * 0.5)]
        for x in check_points:
            r, g, b = pixels[x, y][:3]
            if r > black_threshold or g > black_threshold or b > black_threshold:
                is_black_row = False
                break

        if is_black_row:
            black_row_end = y + 1
        else:
            break

    # 黒い帯があれば削除
    if black_row_end > 0:
        return image.crop((0, black_row_end, width, height))
    return image

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print("3秒後にKindleをフルスクリーンにして開始します。Kindleを最前面に表示してください。")
time.sleep(3)

# フルスクリーンに切り替え
toggle_fullscreen()

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
        cropped = remove_black_bar(screenshot)
        cropped.save(file_path)
        duplicates_to_remove.append(file_path)

        if duplicate_count >= DUPLICATE_THRESHOLD:
            print(f"\n{DUPLICATE_THRESHOLD}回連続で同じ画像が続いたため、終了します。")
            break
    else:
        # 新しい画像の場合
        duplicate_count = 0
        duplicates_to_remove = []  # 重複リストをリセット
        cropped = remove_black_bar(screenshot)
        cropped.save(file_path)
        saved_count += 1
        print(f"{file_name} を保存しました（{saved_count}ページ目）")

    last_pixel_data = current_pixel_data

    # ページをめくる（キー入力 または click(x, y)）
    pyautogui.press(NEXT_PAGE_KEY)
    time.sleep(INTERVAL)

# フルスクリーンを解除
toggle_fullscreen()

# 重複した画像を削除（最初の1枚は残す）
for dup_path in duplicates_to_remove:
    if os.path.exists(dup_path):
        os.remove(dup_path)
        print(f"重複画像を削除: {os.path.basename(dup_path)}")

print(f"\n完了しました！ 合計 {saved_count} ページを保存しました。")
