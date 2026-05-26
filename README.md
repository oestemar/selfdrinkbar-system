# selfdrinkbar-system（セルフ式ドリンクバー販売システム）

ポートフォリオ用の Python3 + Flask + MySQL で構築した飲料管理システムです。

## システム概要

- **カウンター型ドリンク販売システム**: コーヒー、紅茶、お茶、ソフトドリンク等を販売
- **カート機能**: 商品を選択してカートに追加
- **決済機能**: 複数の決済方法に対応（疑似実装）
- **管理者機能**: 商品の登録・編集・削除、CSVインポート/エクスポート、購入履歴管理、パスワード変更

## 技術スタック

- **Backend**: Python 3.x + Flask
- **Database**: MySQL
- **Frontend**: HTML/CSS/JavaScript（テンプレートは別途作成）

## ディレクトリ構造

```
selfdrinkbar-system/
├── app.py  # メインアプリケーション
├── requirements.txt    # Python依存パッケージ
├── .env.example    # 環境変数テンプレート
├── database_schema.sql # DBスキーマ定義
├── README.md   # このファイル
├── templates/  # HTMLテンプレート（別途作成）
│   ├── index.html
│   ├── menu_coffee.html
│   ├── menu_tea.html
│   ├── menu_green_tea.html
│   ├── menu_softdrink.html
│   ├── cart.html
│   ├── checkout.html
│   ├── payment_method.html
│   ├── payment.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_items.html
│   ├── admin_register.html
│   ├── admin_item_edit.html
│   ├── admin_import_export.html
│   ├── admin_search_history.html
│   ├── admin_password.html
│   └── error.html
├── static/ # CSSやJavaScript（別途作成）
│   ├── css/
│   │   └── style.css
│   └── js/
└── docs/   # ドキュメント
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
```

### 4. 管理者ユーザーの作成

```bash
# MySQLで管理者ユーザーを作成（パスワードはハッシュ化済み）
mysql -u root -p selfdrinkbar
INSERT INTO admins (username, password) VALUES ('admin', 'ハッシュ化されたパスワード');
```

> パスワードのハッシュ化は SHA-256 を使用しています。  
> app.py の `hash_password()` 関数で生成できます。

### 5. アプリケーション起動

```bash
# Flask開発サーバー起動
python app.py

# ブラウザでアクセス: http://localhost:5000
```

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
SHA-256 でパスワードをハッシュ化（本番環境では bcrypt 等の使用を推奨）

```python
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
```

## 今後の改善案

- [ ] フロントエンドテンプレートの実装
- [ ] ユーザー登録機能の追加
- [ ] より堅牢なパスワード管理（bcrypt 等）
- [ ] 実際の決済ゲートウェイ連携
- [ ] レスポンシブデザイン対応
- [ ] ユニットテストの追加
- [ ] API エンドポイントの RESTful 化
- [ ] ドキュメントの充実

## ライセンス

このプロジェクトはポートフォリオ用です。

## 注意事項

- このコードは開発・学習目的のための **たたき台** です
- 本番環境での使用にはセキュリティの強化が必要です
- パスワード管理は `bcrypt` 等のより安全な方式を推奨します
- 決済機能は疑似実装のため、実際の運用には決済ゲートウェイの連携が必須です
