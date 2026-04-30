# Hand Hygiene App

手指衛生のアルコール製剤ボトル重量を記録し、使用量を職員別・病棟別に可視化する Flask アプリです。

## 主な機能

- `/input/<staff_id>`: QR から入る個人用入力ページ
- `/staff/<staff_id>`: 個人履歴
- `/calendar/<staff_id>`: 月間カレンダー表示
- `/ranking`: 個人ランキング
- `/ward_ranking`: 病棟ランキング
- `/dashboard`: 病棟ダッシュボード
- `/healthz`: Render ヘルスチェック

## ローカル起動

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

ブラウザで `http://127.0.0.1:8000` を開きます。

## データベース

- 既定では `database.db` を使用します。
- `DB_PATH` を設定すると別の SQLite ファイルを使えます。
- Render では `DB_PATH=/var/data/database.db` を使う前提です。

## 職員マスタ投入

```bash
python3 create_staff.py
```

必要に応じて `DB_PATH` を切り替えると、別DBにも投入できます。

## QR コード生成

```bash
python3 make_qr.py --base-url https://hand-hygiene-app.onrender.com --staff-ids 01001 01002 01003
```

生成された `qr_<staff_id>.png` を配布すると、各職員が直接入力ページにアクセスできます。

## Render デプロイ

このリポジトリは `render.yaml` を使ってデプロイします。

- サービス名: `hand-hygiene-app`
- ランタイム: Python
- 起動コマンド: `gunicorn app:app --bind 0.0.0.0:$PORT`
- 永続ディスク: `/var/data`
- DB パス: `/var/data/database.db`

## 補足

- `database.db` は初期データやローカル確認用としてリポジトリに含まれています。
- 本番では Render Disk 側の DB が優先されます。
