# 分散型図書管理アプリ

## 概要

分散型図書管理アプリを Django で開発します。

## 使用環境

### ■ OS

- 開発環境：

  - Windows 11 + WSL2（Ubuntu 24.04.1 LTS "Noble Numbat"）
  - Python 3.12.3（`venv` による仮想環境）
  - 主にローカルでのコード編集と動作確認に使用

- 実行環境（Docker）：
  - ベースイメージ：`python:3.13-slim-bookworm`（Debian Bookworm ベース）
  - 本番環境・CI/CD 環境で使用し、環境の一貫性を確保
  - ローカルでも Docker を利用可能な構成だが、現在は主に本番環境で稼働

### ■ プログラミング言語

- Python 3.12（開発環境、venv） / 3.13（Docker 実行環境）
- HTML
- CSS
- JavaScript

### ■ フレームワーク・ライブラリ

- Web フレームワーク: Django 5.2
- フロントエンド: Bootstrap 5（crispy-bootstrap5）
- DB ドライバ: psycopg 3.2.9（PostgreSQL）
- テスト: pytest 8.4.1, pytest-django 4.11.1

### ■ ミドルウェア・その他

- アプリケーションサーバー: Gunicorn 23.0.0
- データベース: PostgreSQL

## 進捗状況

- 進捗状況は[こちら](CHANGELOG.md)をご覧ください。

## 開発ドキュメント

- 開発ドキュメントは[こちら](docs/README.md)をご覧ください。

## 必要な環境・依存関係

- **Python バージョン**: 3.12（動作確認済み）
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
