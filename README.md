# 分散型図書管理アプリ

## 概要
分散型図書管理アプリをDjangoで開発します。

## 進捗状況
- 進捗状況は[こちら](CHANGELOG.md)をご覧ください。

## 開発ドキュメント
- 開発ドキュメントは[こちら](docs/README.md)をご覧ください。

## 必要な環境・依存関係
- **Pythonバージョン**: 3.12（動作確認済み）
- **依存ライブラリ**:
  - Django 5.2

## セットアップ手順

```bash
# Pythonの仮想環境を作成します（初回のみ）
python3 -m venv .venv
# 仮想環境を有効化します
source .venv/bin/activate
# 必要なライブラリをインストールします
pip install -r requirements.txt
# マイグレーションを行います。
python manage.py migrate
# ローカルサーバーを起動します。
python manage.py runserver
# その後、ブラウザで`http://127.0.0.1:8000/`にアクセスしてください。
```