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
- HTML/CSS/JavaScript

### ■ フレームワーク・ライブラリ

| 種類               | 名称                          | バージョン     | 備考                             |
| ------------------ | ----------------------------- | -------------- | -------------------------------- |
| Web フレームワーク | Django                        | 5.2            |                                  |
| フロントエンド     | Bootstrap (crispy-bootstrap5) | 5              | CDN 利用＋フォームスタイルに利用 |
| DB ドライバ        | psycopg                       | 3.2.9          | PostgreSQL 用                    |
| テスト             | pytest / pytest-django        | 8.4.1 / 4.11.1 |                                  |

### ■ ミドルウェア・その他

| 種類                     | 名称       | バージョン | 備考 |
| ------------------------ | ---------- | ---------- | ---- |
| アプリケーションサーバー | Gunicorn   | 23.0.0     |      |
| データベース             | PostgreSQL | -          |      |

## デプロイ・実行環境

- 本番環境 URL (Cloud Run): https://distributed-library-1066453624488.asia-northeast1.run.app/

  ※ Cloud Run はサーバレス環境のため、初回アクセス時にコールドスタートが発生し、約 10 秒程度の起動時間がかかる場合があります。
  また、起動後のレスポンスも 1〜3 秒ほどかかることがあります。あらかじめご了承ください。

- 代替環境 URL (Render - Python 環境): https://distributed-library-2.onrender.com

  ※ Render の無料プランを使っており、初回起動に約 1 分程度かかる場合がありますが、起動後は比較的高速に応答します。

- 代替環境 URL (Render - Docker 環境):https://distributed-library-q6cj.onrender.com

  ※ Docker 環境でも同様に初回起動に時間がかかる場合がありますが、動作環境の違いを確認いただけます。

- 備考: テスト用アカウント情報（以下のアカウントはテスト目的で用意されたものです）

  | 役割           | ユーザー名 | パスワード          |
  | -------------- | ---------- | ------------------- |
  | 一般ユーザー 1 | general1   | dev_general1_123    |
  | 一般ユーザー 2 | general2   | dev_general2_123    |
  | 司書           | librarian1 | dev_librarian1_123! |

  > ※これらのアカウントはテスト用です。本番環境の重要な情報は含まれていません。

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
