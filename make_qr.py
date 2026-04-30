import argparse
from pathlib import Path

import qrcode


def parse_args():
    parser = argparse.ArgumentParser(description="入力ページ用 QR コードを生成します。")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="入力ページのベースURL。例: https://hand-hygiene-app.onrender.com",
    )
    parser.add_argument(
        "--staff-ids",
        nargs="+",
        default=["10001", "10002", "10003"],
        help="QR を作成するスタッフIDの一覧",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="QR 画像の出力先ディレクトリ",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for staff_id in args.staff_ids:
        url = f"{base_url}/input/{staff_id}"
        img = qrcode.make(url)
        img.save(output_dir / f"qr_{staff_id}.png")
        print(f"saved: qr_{staff_id}.png -> {url}")


if __name__ == "__main__":
    main()
