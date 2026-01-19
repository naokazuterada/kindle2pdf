from PIL import Image
from pypdf import PdfReader, PdfWriter
import os
import glob
import sys

# --- 設定項目 ---
SAVE_DIR = "output/screenshots"  # 画像が保存されているフォルダ
OUTPUT_PDF = "output/books/book.pdf"   # 出力するPDFファイル名
MAX_SIZE_MB = 32  # NotebookLMの上限サイズ（MB）
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
# ----------------

def get_file_size_mb(file_path):
    """ファイルサイズをMB単位で取得"""
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

def split_pdf(input_pdf_path):
    """PDFを32MB以下のファイルに分割"""

    # ファイルサイズをチェック
    file_size_mb = get_file_size_mb(input_pdf_path)
    print(f"\nPDFファイルサイズ: {file_size_mb:.2f} MB")

    if file_size_mb <= MAX_SIZE_MB:
        print(f"ファイルサイズが {MAX_SIZE_MB}MB 以下のため、分割の必要はありません")
        return

    # PDFを読み込み
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    print(f"総ページ数: {total_pages}")

    # 1ページあたりの平均サイズを計算
    avg_size_per_page = os.path.getsize(input_pdf_path) / total_pages

    # 32MB以下に収まる推定ページ数を計算（安全のため90%で計算）
    safety_factor = 0.9
    estimated_pages_per_file = int((MAX_SIZE_BYTES * safety_factor) / avg_size_per_page)

    if estimated_pages_per_file < 1:
        estimated_pages_per_file = 1

    print(f"1ファイルあたりの推定ページ数: {estimated_pages_per_file}")

    # 出力フォルダを作成
    base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
    output_dir = os.path.join(os.path.dirname(input_pdf_path), base_name)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"出力フォルダを作成: {output_dir}")

    # PDFを分割
    file_number = 1
    current_page = 0

    while current_page < total_pages:
        writer = PdfWriter()
        start_page = current_page
        temp_path = None

        # ページを追加しながらサイズをチェック
        while current_page < total_pages:
            writer.add_page(reader.pages[current_page])
            current_page += 1

            # 一時ファイルに保存してサイズをチェック
            temp_path = os.path.join(output_dir, f"_temp_{file_number}.pdf")
            with open(temp_path, "wb") as output_file:
                writer.write(output_file)

            current_size = os.path.getsize(temp_path)

            # 32MBを超えたら1ページ戻して確定
            if current_size > MAX_SIZE_BYTES:
                if current_page - start_page == 1:
                    # 1ページでも32MBを超える場合はそのまま保存
                    print(f"警告: {current_page}ページ目が単体で32MBを超えています")
                    break
                else:
                    # 1ページ戻す
                    current_page -= 1
                    writer = PdfWriter()
                    for i in range(start_page, current_page):
                        writer.add_page(reader.pages[i])
                    break

            # 推定ページ数に達したらファイルを確定
            if current_page - start_page >= estimated_pages_per_file:
                break

        # 最終的なファイル名で保存
        output_filename = f"{file_number:04d}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        # 一時ファイルを削除
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        final_size_mb = get_file_size_mb(output_path)
        page_range = f"{start_page + 1}-{current_page}"
        print(f"作成: {output_filename} ({page_range}ページ, {final_size_mb:.2f} MB)")

        file_number += 1

    print(f"\n完了: {file_number - 1} 個のPDFファイルに分割しました")
    print(f"出力先: {output_dir}")

def create_pdf_from_images(save_dir, output_pdf):
    """画像からPDFを作成"""
    # 出力先フォルダを作成（存在しない場合）
    output_dir = os.path.dirname(output_pdf)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 画像ファイルを取得してソート
    image_files = sorted(glob.glob(os.path.join(save_dir, "*.png")))

    if not image_files:
        print(f"エラー: {save_dir} フォルダに画像がありません")
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
        output_pdf,
        save_all=True,
        append_images=other_images
    )

    print(f"完了: {output_pdf} を作成しました")
    return output_pdf

if __name__ == "__main__":
    # コマンドライン引数でPDFパスが指定された場合は分割のみ実行
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if not os.path.exists(pdf_path):
            print(f"エラー: {pdf_path} が見つかりません")
            exit(1)
        split_pdf(pdf_path)
    else:
        # 画像からPDFを作成
        pdf_path = create_pdf_from_images(SAVE_DIR, OUTPUT_PDF)
        # 作成したPDFを自動的に分割チェック
        split_pdf(pdf_path)
