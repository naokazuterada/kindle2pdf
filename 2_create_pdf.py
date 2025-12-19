from PIL import Image
import os
import glob

# --- 設定項目 ---
SAVE_DIR = "output/screenshots"  # 画像が保存されているフォルダ
OUTPUT_PDF = "output/book.pdf"   # 出力するPDFファイル名
# ----------------

# 画像ファイルを取得してソート
image_files = sorted(glob.glob(os.path.join(SAVE_DIR, "*.png")))

if not image_files:
    print(f"エラー: {SAVE_DIR} フォルダに画像がありません")
    exit(1)

print(f"{len(image_files)} 枚の画像を見つけました")

# 最初の画像を開く
first_image = Image.open(image_files[0]).convert("RGB")

# 残りの画像を開く
other_images = []
for f in image_files[1:]:
    img = Image.open(f).convert("RGB")
    other_images.append(img)

# PDFとして保存
first_image.save(
    OUTPUT_PDF,
    save_all=True,
    append_images=other_images
)

print(f"完了: {OUTPUT_PDF} を作成しました")
