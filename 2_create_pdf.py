from PIL import Image
from pypdf import PdfReader, PdfWriter
import os
import glob
import re
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
        output_filename = f"{file_number:03d}.pdf"
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

def natural_sort_key(path):
    """ファイル名の数字部分を数値として比較するためのキー"""
    name = os.path.basename(path)
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", name)]

def report_missing_numbers(image_files):
    """ファイル名の番号に欠番がある場合に通知する（処理は止めない）"""
    numbers = []
    for path in image_files:
        digits = re.findall(r"\d+", os.path.basename(path))
        if digits:
            numbers.append(int(digits[-1]))

    if len(numbers) < 2:
        return

    missing = sorted(set(range(min(numbers), max(numbers) + 1)) - set(numbers))
    if missing:
        preview = ", ".join(str(n) for n in missing[:20])
        if len(missing) > 20:
            preview += f", ... 他 {len(missing) - 20} 件"
        print(f"欠番あり（削除済みページと思われます / {len(missing)} 件）: {preview}")
        print("→ 欠番は飛ばして、残りの画像をすべて結合します")

def iter_images(image_files, skipped):
    """画像を1枚ずつ開いて返す（読み込めないファイルは飛ばす）"""
    for index, path in enumerate(image_files, 1):
        try:
            with Image.open(path) as img:
                yield img.convert("RGB")
        except Exception as e:
            skipped.append((path, e))
            print(f"警告: {os.path.basename(path)} を読み込めませんでした（スキップ）: {e}")
            continue

def create_pdf_from_images(save_dir, output_pdf):
    """画像からPDFを作成"""
    # 出力先フォルダを作成（存在しない場合）
    output_dir = os.path.dirname(output_pdf)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 画像ファイルを取得してソート（番号順・欠番があってもそのまま続行）
    image_files = sorted(glob.glob(os.path.join(save_dir, "*.png")),
                         key=natural_sort_key)

    if not image_files:
        print(f"エラー: {save_dir} フォルダに画像がありません")
        exit(1)

    print(f"{len(image_files)} 枚の画像を見つけました")
    report_missing_numbers(image_files)

    # 先頭の使える画像を探す（壊れているファイルは飛ばす）
    skipped = []
    first_image = None
    first_index = 0
    for index, path in enumerate(image_files):
        try:
            with Image.open(path) as img:
                first_image = img.convert("RGB")
            first_index = index
            break
        except Exception as e:
            skipped.append((path, e))
            print(f"警告: {os.path.basename(path)} を読み込めませんでした（スキップ）: {e}")

    if first_image is None:
        print("エラー: 読み込める画像が1枚もありませんでした")
        exit(1)

    # PDFとして保存（メモリ節約のため1枚ずつ開いて渡す）
    first_image.save(
        output_pdf,
        save_all=True,
        append_images=iter_images(image_files[first_index + 1:], skipped)
    )

    used_count = len(image_files) - len(skipped)
    print(f"完了: {output_pdf} を作成しました（{used_count} ページ）")
    if skipped:
        print(f"読み込めずスキップした画像: {len(skipped)} 件")
        for path, e in skipped:
            print(f"  - {os.path.basename(path)}: {e}")
    return output_pdf

if __name__ == "__main__":
    # コマンドライン引数でPDFパスが指定された場合は分割のみ実行
    if len(sys.argv) > 1:
        # 複数のPDFファイルを処理
        pdf_paths = sys.argv[1:]
        total_files = len(pdf_paths)

        for index, pdf_path in enumerate(pdf_paths, 1):
            print(f"\n{'='*60}")
            print(f"[{index}/{total_files}] 処理中: {pdf_path}")
            print(f"{'='*60}")

            if not os.path.exists(pdf_path):
                print(f"エラー: {pdf_path} が見つかりません（スキップします）")
                continue

            split_pdf(pdf_path)

        print(f"\n{'='*60}")
        print(f"完了: {total_files} 個のファイルを処理しました")
        print(f"{'='*60}")
    else:
        # 画像からPDFを作成
        pdf_path = create_pdf_from_images(SAVE_DIR, OUTPUT_PDF)
        # 作成したPDFを自動的に分割チェック
        split_pdf(pdf_path)
