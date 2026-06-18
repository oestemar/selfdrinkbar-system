from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import io
import csv

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

try:
    mysql = MySQL(app)
    print("=== MySQL initialized successfully ===")
except Exception as e:
    print("=== MySQL init error ===", e)

# ==================== ユーティリティ関数 ====================
def hash_password(password):
    """パスワードをハッシュ化"""
    return generate_password_hash(password)

def admin_login_required(f):
    """管理者ログイン確認デコレータ"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') == 'demo' and request.method == 'POST':
            return render_template(
                'admin/admin_error.html', 
                message='デモアカウントは閲覧のみ可能です（操作は出来ません）'
                )
        return f(*args, **kwargs)
    return wrapper

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
    """, ('demo', 'demo', 'scrypt:32768:8:1$WRfRG37kry4bNlz3$d5ff0e0091cecd2bd97f1f11309c3f5116eb017750972b8bc107de7b05102eb4412313ecc5c46cd40c63bec46241ffceb4ba22c98577e67a3f4dea17655912dd'
))

    cursor.execute("""
        INSERT INTO admins (username, role, created_at, updated_at, password_hash)
        VALUES (%s, %s, NOW(), NOW(), %s)
    """, ('admin', 'admin', 'scrypt:32768:8:1$GngpvBvxaKZhgDTY$d9302c1c1d2ba7373b9420127f3444b1dcecb359991c8a48425b0c11a7753015c2dcd2fc579f0f04f95b0e223679d192e8320fc7195d619a014751efb42360c0'
))

    mysql.connection.commit()
    cursor.close()

    return "Initial admins (demo, admin) created"

# ==================== メニュー関連ルート ====================
@app.route('/')
def index():
    return redirect(url_for('menu_coffee'))

@app.context_processor
def inject_cart_count():
    cart = session.get('cart', [])
    cart_count = sum(item['quantity'] for item in cart)
    return dict(cart_count=cart_count)

@app.route('/menu/coffee', methods=['GET'])
def menu_coffee():
    """コーヒーメニュー表示"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM items WHERE category = 'coffee'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_coffee.html', items=items, category="coffee", step="menu")
    except Exception as e:
        return render_template('error.html', message=str(e))

@app.route('/menu/tea', methods=['GET'])
def menu_tea():
    """紅茶メニュー表示"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM items WHERE category = 'tea'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_tea.html', items=items, category="tea", step="menu")
    except Exception as e:
        return render_template('error.html', message=str(e))

@app.route('/menu/green_tea', methods=['GET'])
def menu_green_tea():
    """お茶メニュー表示"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM items WHERE category = 'green_tea'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_green_tea.html', items=items, category="green_tea", step="menu")
    except Exception as e:
        return render_template('error.html', message=str(e))



@app.route('/menu/softdrink', methods=['GET'])
def menu_softdrink():
    """ソフトドリンクメニュー表示"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM items WHERE category = 'softdrink'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_softdrink.html', items=items, category="softdrink", step="menu")
    except Exception as e:
        return render_template('error.html', message=str(e))


# ==================== カート関連ルート ====================
@app.route('/cart', methods=['GET'])
def view_cart():
    """カート表示"""
    cart = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total_price=total_price, step="cart")


@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """カートに商品を追加"""
    try:
        item_id = request.form.get('item_id')
        quantity = int(request.form.get('quantity', 1))

        if not item_id:
            return jsonify({'success': False, 'message': '商品IDがありません'}), 400        

        if 'cart' not in session:
            session['cart'] = []

        # 既存のカート内容から商品を検索
        for item in session['cart']:
            if str(item['id']) == str(item_id):
                item['quantity'] += quantity
                item['subtotal'] = item['price'] * item['quantity']   
                session.modified = True
                return jsonify({'success': True, 'cart_count': sum(i['quantity'] for i in session['cart'])})
        
        # 商品情報を取得
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, name, price FROM items WHERE id = %s", (item_id,))
        product = cursor.fetchone()
        cursor.close()

        if not product:
            return jsonify({'success': False, 'message': '商品が見つかりません'}), 404

        session['cart'].append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'subtotal': product['price'] * quantity
        })
        session.modified = True
        
        return jsonify({'success': True, 'cart_count': sum(i['quantity'] for i in session['cart'])})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    """カートから商品を削除"""
    try:
        item_id = request.form.get('item_id')
        
        if not item_id:
            return jsonify({'success': False, 'message': '商品IDがありません'}), 400

        if 'cart' in session:
            session['cart'] = [item for item in session['cart'] if str(item['id']) != str(item_id)]
            session.modified = True
            return redirect(url_for('view_cart'))
        
        return "カートが空です", 400
    except Exception as e:
        return render_template('error.html', message=str(e))

# ==================== 決済関連ルート ====================
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """精算内容確認"""
    if request.method == 'GET':
        cart = session.get('cart', [])
        total_price = sum(item['price'] * item['quantity'] for item in cart)
        total_price = int(total_price)  # 小数点以下切り捨て
        return render_template('checkout.html', cart=cart, total_price=total_price, step="checkout")
    else:
        # POST: 精算情報を確認
        return redirect(url_for('payment_method'))


@app.route('/payment_method', methods=['GET'])
def payment_method():
    """決済方法選択"""
    cart = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('payment_method.html', total_price=total_price, step="payment_method")


@app.route('/payment', methods=['POST'])
def payment():
    """決済処理（疑似）"""
    try:
        payment_method = request.form.get('method')
        session['payment_method'] = payment_method        

        if not payment_method:
            return render_template('payment_method.html', total_price=0, error='決済方法を選択してください')
        
        if payment_method not in ['cash', 'card', 'paspo', 'qr']:
            return render_template('payment_method.html', total_price=0, error='無効な決済方法です')

        # 決済方法毎に各決済画面へ遷移
        if payment_method == 'cash':
            return render_template('payment_01_cash.html', method='現金', total_price=sum(item['price'] * item['quantity'] for item in session.get('cart', [])), step="payment")        
        if payment_method == 'card':
            return render_template('payment_02_credit.html', method='クレジットカード', total_price=sum(item['price'] * item['quantity'] for item in session.get('cart', [])), step="payment")
        if payment_method == 'paspo':
            return render_template('payment_03_paspo.html', method='pasmo', total_price=sum(item['price'] * item['quantity'] for item in session.get('cart', [])), step="payment")
        if payment_method == 'qr':
            return render_template('payment_04_qr.html', method='QRコード', total_price=sum(item['price'] * item['quantity'] for item in session.get('cart', [])), step="payment")

    except Exception as e:
        return render_template('error.html', message=str(e))


@app.route('/payment/complete', methods=['POST'])
def payment_complete():
    """決済完了"""
    try:
        cart = session.get('cart', [])

        if not cart:
            return "カートが空です", 400

        total_price = sum(item['price'] * item['quantity'] for item in cart)
        payment_method = session.get('payment_method')
        
        # 購入履歴をDBに保存
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # 注文テーブルに挿入
        cursor.execute("""
            INSERT INTO orders (total, payment_method, purchase_datetime)
            VALUES (%s, %s, %s)
        """, (total_price, payment_method, datetime.now()))
        
        order_id = cursor.lastrowid
        
        # 注文詳細テーブルに挿入
        for item in cart:
            cursor.execute("""
                INSERT INTO order_details (ordered_id, item_id, name, price, quantity, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, item['id'], item['name'], item['price'], item['quantity'], item['subtotal']))
        
        mysql.connection.commit()
        cursor.close()
        
        # カートをクリア
        session.pop('cart', None)
        session.modified = True
        
        return render_template('payment_complete.html', step="complete")
    except Exception as e:
        mysql.connection.rollback()
        return render_template('error.html', message=str(e))

# ==================== 管理者ログイン ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理者ログイン"""
    if request.method == 'GET':
        return render_template('admin/login.html', login_page=True)
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        print(username)
        print(password)
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                "SELECT * FROM admins WHERE username = %s",
                (username,)
            )
            admin = cursor.fetchone()
            print(admin)
            cursor.close()
            
            if admin and check_password_hash(admin['password_hash'], password):
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['username']
                session['role'] = admin['role']
                session.modified = True
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('admin/login.html', message='ユーザー名またはパスワードが間違っています')
        except Exception as e:
            return render_template('admin/login.html', message=str(e))


# ==================== 管理者ダッシュボード ====================
@app.route('/admin/dashboard', methods=['GET'])
@admin_login_required
def admin_dashboard():
    """管理者メニュー"""
    return render_template('admin/dashboard.html')


# ==================== 管理者・商品管理 ====================
@app.route('/admin/items', methods=['GET', 'POST'])
@admin_login_required
def admin_items():
    """商品検索・一覧"""
    if request.method == 'GET':
        search_keyword = request.args.get('search', '')
        category = request.args.get('category', '')
        
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            query = "SELECT * FROM items WHERE 1=1"
            params = []
            
            if search_keyword:
                query += " AND name LIKE %s"
                params.append(f"%{search_keyword}%")
            
            if category:
                query += " AND category = %s"
                params.append(category)
            
            cursor.execute(query, params)
            items = cursor.fetchall()
            cursor.close()
            
            return render_template('admin/items.html', items=items)
        except Exception as e:
            return render_template('admin/admin_error.html', message=str(e))
    else:
        # POST: 検索実行
        return redirect(url_for('admin_items', 
                               search=request.form.get('search'),
                               category=request.form.get('category')))


@app.route('/admin/register', methods=['GET', 'POST'])
@admin_login_required
@admin_only
def admin_register():
    """商品登録"""
    if request.method == 'GET':
        return render_template('admin/register.html')
    else:
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            price = request.form.get('price')
            description = request.form.get('description')
            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""
                INSERT INTO items (name, category, price, description, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, category, price, description, datetime.now()))
            
            mysql.connection.commit()
            cursor.close()

            flash("商品を登録しました")
            return redirect(url_for('admin_items'))
        except Exception as e:
            return render_template('admin/admin_error.html', message=str(e))

@app.route('/admin/item_edit/<int:item_id>', methods=['GET', 'POST'])
@admin_login_required
@admin_only
def admin_item_edit(item_id):
    """商品編集"""
    try:
        if request.method == 'GET':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            cursor.close()
            
            if not item:
                return render_template('admin/error.html', message='商品が見つかりません'), 404
            
            return render_template('admin/item_edit.html', item=item)
        else:
            name = request.form.get('name')
            category = request.form.get('category')
            price = request.form.get('price')
            description = request.form.get('description')
            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""
                UPDATE items SET name = %s, category = %s, price = %s, description = %s
                WHERE id = %s
            """, (name, category, price, description, item_id))
            
            mysql.connection.commit()
            cursor.close()

            flash("商品を更新しました")
            return redirect(url_for('admin_items'))
    except Exception as e:
        return render_template('admin/admin_error.html', message=str(e))

@app.route('/admin/item_delete', methods=['POST'])
@admin_login_required
@admin_only
def admin_item_delete():
    """商品削除"""
    try:
        item_id = request.form.get('item_id')
        
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
        mysql.connection.commit()
        cursor.close()

        flash("商品を削除しました")
        return redirect(url_for('admin_items'))
    except Exception as e:
        return render_template('admin/admin_error.html', message=str(e))

# ==================== 管理者・CSVインポート/エクスポート ====================
@app.route('/admin/import_export', methods=['GET', 'POST'])
@admin_login_required
@admin_only
def admin_import_export():
    """CSVインポート/エクスポート"""
    if request.method == 'GET':
        return render_template('admin/import_export.html')
    else:
        action = request.form.get('action')
        
        if action == 'export':
            # エクスポート処理
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT id, name, category, price, description FROM items")
                items = cursor.fetchall()
                cursor.close()
                
                # CSV形式で返す
                csv_data = "id,name,category,price,description\n"
                for item in items:
                    csv_data += f"{item['id']},{item['name']},{item['category']},{item['price']},{item['description']}\n"
                
                csv_data = '\ufeff' + csv_data  # UTF-8 BOMを追加
                return csv_data, 200, {'Content-Disposition': 'attachment; filename=items.csv'}
            except Exception as e:
                return render_template('admin/import_export.html', message=str(e))
        
        elif action == 'import':
            try:
                file = request.files.get('file')

                if not file:
                    return render_template('admin/admin_error.html', message="CSVファイルが選択されていません")

                # ① items テーブルを初期化（全削除 + AUTO_INCREMENT リセット）
                cursor = mysql.connection.cursor()
                # items のみ全削除（履歴は残す）
                cursor.execute("DELETE FROM items")
                # AUTO_INCREMENT をリセット
                cursor.execute("ALTER TABLE items AUTO_INCREMENT = 1")
                mysql.connection.commit()

                # CSV を UTF-8(BOM付き) で読み込む
                stream = io.TextIOWrapper(file.stream, encoding='utf-8-sig')
                reader = csv.reader(stream)

                # 1行目（ヘッダー）をスキップ
                header = next(reader, None)

                imported_count = 0

                for row in reader:
                    # 空行スキップ
                    if not row or len(row) < 4:
                        continue

                    name = row[0].strip()
                    category = row[1].strip()
                    price = int(row[2])
                    description = row[3].strip()

                    # INSERT
                    cursor.execute("""
                        INSERT INTO items (name, category, price, description)
                        VALUES (%s, %s, %s, %s)
                    """, (name, category, price, description))

                    imported_count += 1

                mysql.connection.commit()
                cursor.close()

                flash(f"{imported_count} 件のデータをインポートしました")
                return redirect(url_for('admin_import_export'))

            except Exception as e:
                return render_template('admin/admin_error.html', message=str(e))


# ==================== 管理者・購入履歴検索 ====================
@app.route('/admin/search_history', methods=['GET', 'POST'])
@admin_login_required
def admin_search_history():
    """購入履歴検索"""
    search = request.form.get('search', '')
    date = request.form.get('date', '')
        
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        query = """
            SELECT 
                o.id AS id,
                o.total AS total,
                o.payment_method,
                o.purchase_datetime,
                d.item_id,
                d.name AS name,
                d.price AS price,
                d.quantity AS quantity,
                d.subtotal AS subtotal
            FROM orders o
            LEFT JOIN order_details d ON o.id = d.ordered_id
            WHERE 1=1
        """
        params = []
            
        # 注文ID・商品名・商品IDなどのキーワード検索
        if search:
            query += """
                AND (
                    o.id LIKE %s OR
                    d.name LIKE %s OR
                    d.item_id LIKE %s
                )
            """
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        # 日付検索
        if date:
            query += " AND DATE(o.purchase_datetime) = %s"
            params.append(date)

        cursor.execute(query, params)
        orders = cursor.fetchall()
        cursor.close()
            
        return render_template(
            'admin/search_history.html',
            orders=orders,
            search=search,
            date=date
        )
    except Exception as e:
        return render_template('admin/admin_error.html', message=str(e))

# ==================== 管理者・パスワード変更 ====================
@app.route('/admin/password', methods=['GET', 'POST'])
@admin_login_required
@admin_only
def admin_password():
    """パスワード変更"""
    if request.method == 'GET':
        return render_template('admin/password.html')
    else:
        try:
            current_password = request.form.get('current')
            new_password = request.form.get('new')
            confirm_password = request.form.get('confirm')
            
            if new_password != confirm_password:
                return render_template('admin/password.html', error='新しいパスワードが一致しません')
            
            admin_id = session.get('admin_id')
            
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT password_hash FROM admins WHERE id = %s", (admin_id,))
            admin = cursor.fetchone()
            
            if not admin or not check_password_hash(admin['password_hash'], current_password):
                cursor.close()
                return render_template('admin/password.html', error='現在のパスワードが正しくありません')
            
            cursor.execute(
                "UPDATE admins SET password_hash = %s WHERE id = %s",
                (hash_password(new_password), admin_id)
            )
            
            mysql.connection.commit()
            cursor.close()
            
            return render_template('admin/password.html', message='パスワードを変更しました')
        except Exception as e:
            return render_template('admin/admin_error.html', message=str(e))


# ==================== その他のルート ====================
@app.route('/reset')
def reset():
    session.clear()
    return "session cleared"

@app.route('/admin/logout', methods=['GET'])
def admin_logout():
    """ログアウト"""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('role', None)
    session.modified = True
    return redirect(url_for('admin_login'))

@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラ"""
    return render_template('error.html', message='ページが見つかりません'), 404

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/admin'):
        return render_template('admin/admin_error.html', message='ページが見つかりません'), 404
    return render_template('error.html', message='ページが見つかりません'), 404

@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラ"""
    mysql.connection.rollback()
    return render_template('error.html', message='サーバーエラーが発生しました'), 500

@app.errorhandler(500)
def internal_error(error):
    mysql.connection.rollback()
    if request.path.startswith('/admin'):
        return render_template('admin/admin_error.html', message='サーバーエラーが発生しました'), 500
    return render_template('error.html', message='サーバーエラーが発生しました'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
