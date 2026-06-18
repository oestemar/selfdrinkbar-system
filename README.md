# selfdrinkbar-system（セルフ式ドリンクバー販売システム）

ポートフォリオ用の Python3 + Flask + MySQL で構築した飲料管理システムです。

## システム概要

- **カウンター型ドリンク販売システム**: コーヒー、紅茶、お茶、ソフトドリンク等を販売
- **カート機能**: 商品を選択してカートに追加
- **決済機能**: 複数の決済方法に対応（疑似実装）
- **管理者機能**: 商品の登録・編集・削除、CSVインポート/エクスポート、購入履歴管理、パスワード変更

## [テスト手順書](/docs/test_document.md)

テスト手順書は上記リンクをご参照ください

## 技術スタック

- **Backend**: Python 3.x + Flask
- **Database**: MySQL
- **Frontend**: HTML/CSS/JavaScript（テンプレートは別途作成）,Bootstrap

## ディレクトリ構造

```
selfdrinkbar-system/
├── app.py  # メインアプリケーション
├── requirements.txt    # Python依存パッケージ
├── .env.example    # 環境変数テンプレート
├── config.py   # DBの環境変数取得コード
├── database_schema.sql # DBスキーマ定義
├── README.md   # このファイル
├── templates/  # HTMLテンプレート（別途作成）
│   ├── base.html
│   ├── menu_coffee.html
│   ├── menu_tea.html
│   ├── menu_green_tea.html
│   ├── menu_softdrink.html
│   ├── cart.html
│   ├── checkout.html
│   ├── payment_method.html
│   ├── payment_01_cash.html
│   ├── payment_02_credit.html
│   ├── payment_03_paspo.html
│   ├── payment_04_qr.html
│   ├── payment_complete.html
│   ├── error.html
│   └── admin
│       ├── admin_base.html
│       ├── dashboard.html
│       ├── items_edit.html
│       ├── items.html
│       ├── register.html
│       ├── item_edit.html
│       ├── import_export.html
│       ├── search_history.html
│       ├── password.html
│       └── admin_error.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── img/
│   │   ├── ic_reader.png
│   │   └── qr_sample.png
│   └── js/
│   │   └── cart.js
└── docs/   # ドキュメント
    ├── DB詳細設計.xlsx
    ├── 画面一覧.xlsx
    ├── システム仕様書.docx
    ├── ER図.png    
    └── hash値設定SQL.txt
```

## セットアップ手順

### 1. 環境構築

```bash
# リポジトリのクローン
cd selfdrinkbar-system

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化（Windows）
venv\Scripts\activate

# 仮想環境の有効化（Mac/Linux）
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 2. データベースセットアップ

```bash
# MySQLサーバーに接続
mysql -u root -p

# SQLスクリプトを実行
source database_schema.sql;

# または、コマンドラインから実行
mysql -u root -p < database_schema.sql
```

### 3. 環境変数設定

```bash
# .env.example をコピーして .env を作成
cp .env.example .env

# .env ファイルを編集して、以下を設定：
# - MYSQL_HOST: MySQLサーバーのホスト（デフォルト: localhost）
# - MYSQL_USER: MySQLユーザー名（デフォルト: root）
# - MYSQL_PASSWORD: MySQLパスワード
# - MYSQL_DB: データベース名（デフォルト: selfdrinkbar）
# - SECRET_KEY: Flask秘密キー（本番環境では安全なキーに変更）
# - FLASK_APP=app.py
# - FLASK_ENV=development
# - FLASK_DEBUG=True
```

### 4. DBのadminsテーブルに管理者アカウントを登録する（ローカルにシステム環境を構築する場合に必要）

```app.pyに下記コードがあり、プロジェクト直下の「/init_admins」をURLに追記してEnterを押すと実行され、管理者アカウントがDBに登録されます。/init_adminsへブラウザでアクセスしない限り実行されません。

# 管理者アカウント登録（一回だけ）
@app.route('/init_admins')
def init_admins():
    from app import mysql  # もし必要なら

    cursor = mysql.connection.cursor()

    # すでに admin が存在するなら実行しない
    cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
    existing = cursor.fetchone()
    if existing:
        return "Admins already created", 403

    # INSERT
    cursor.execute("""
        INSERT INTO admins (username, role, created_at, updated_at, password_hash)
        VALUES (%s, %s, NOW(), NOW(), %s)
    """, ('demo', 'demo', '自分で決めたパスワードのハッシュ値'
))

    cursor.execute("""
        INSERT INTO admins (username, role, created_at, updated_at, password_hash)
        VALUES (%s, %s, NOW(), NOW(), %s)
    """, ('admin', 'admin', '自分で決めたパスワードのハッシュ値'
))

    mysql.connection.commit()
    cursor.close()

    return "Initial admins (demo, admin) created"

```
#### ハッシュ値の生成方法
> パスワードのハッシュ化は SHA-256 を使用しています。  
> 'ハッシュ値'のところに記述するハッシュ値は下記で生成できます。
from werkzeug.security import generate_password_hash
print(generate_password_hash("好きなパスワード"))

### 5. アプリケーション起動

```bash
# Flask開発サーバー起動　※プロジェクトフォルダ内で下記コマンド実行
flask run

# ブラウザでアクセス: http://localhost:5000
```

### 6. CSVインポート（商品一覧の取り込み）
- 管理者ログイン後、メニューのCSVインポートで/data/items.csvを取り込む ※CSVはdataフォルダに置いてあります。

## ルーティング一覧

### メニュー
- `GET /menu/coffee` - コーヒーメニュー表示
- `GET /menu/tea` - 紅茶メニュー表示
- `GET /menu/green_tea` - お茶メニュー表示
- `GET /menu/softdrink` - ソフトドリンクメニュー表示

### カート
- `GET /cart` - カート表示
- `POST /cart/add` - カートに商品追加
- `POST /cart/remove` - カートから商品削除

### 決済
- `GET/POST /checkout` - 精算内容確認
- `GET /payment_method` - 決済方法選択
- `POST /payment` - 決済処理（疑似）
- `POST /payment/complete` - 決済完了

### 管理者
- `GET/POST /admin/login` - 管理者ログイン
- `GET /admin/dashboard` - 管理者ダッシュボード
- `GET/POST /admin/items` - 商品検索・一覧
- `GET/POST /admin/register` - 商品登録
- `GET/POST /admin/item_edit/<id>` - 商品編集
- `POST /admin/item_delete` - 商品削除
- `GET/POST /admin/import_export` - CSVインポート/エクスポート
- `GET/POST /admin/search_history` - 購入履歴検索
- `GET/POST /admin/password` - パスワード変更

## 使用技術の詳細

### Flask-MySQLdb
MySQL との接続を管理するための Flask 拡張機能

```python
from flask_mysqldb import MySQL
mysql = MySQL(app)
```

### セッション管理
Flask のセッション機能でカート情報と管理者情報を管理

```python
session['cart'] = []
session['admin_id'] = admin_id
```

### パスワードハッシュ化
SHA-256 でパスワードをハッシュ化
管理者ログイン画面で入力したパスワードは下記関数により内部でハッシュ化されて使用されます。DBに登録するとき登録しておいたハッシュ値と照合し、ログイン認証します。

```python
def hash_password(password):
    """パスワードを安全にハッシュ化（PBKDF2-SHA256）"""
    return generate_password_hash(password)
```

## ライセンス

このプロジェクトはポートフォリオ用です。

## 注意事項

- このコードは開発・学習目的のための **たたき台** です
- 本番環境での使用にはセキュリティの強化が必要です
- パスワード管理は `bcrypt` 等のより安全な方式を推奨します
- 決済機能は疑似実装のため、実際の運用には決済ゲートウェイの連携が必須です
