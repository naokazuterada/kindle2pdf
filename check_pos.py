import pyautogui
import time

print("5秒後にマウスの座標を表示します。ボタンの上に置いてください...")
time.sleep(5)
print(f"現在のマウス座標: {pyautogui.position()}")
