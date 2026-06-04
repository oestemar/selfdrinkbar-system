from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime
import hashlib
import os
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

mysql = MySQL(app)

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
        if session.get('role') != 'admin':
            return render_template('admin/admin_error.html', message="この操作は管理者のみ可能です")
        return f(*args, **kwargs)
    return wrapper

# ==================== メニュー関連ルート ====================
@app.route('/')
def index():
    return render_template('menu_coffee.html')

@app.route('/menu/coffee', methods=['GET'])
def menu_coffee():
    """コーヒーメニュー表示"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE category = 'coffee'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_coffee.html', items=items)
    except Exception as e:
        return render_template('error.html', message=str(e))


@app.route('/menu/tea', methods=['GET'])
def menu_tea():
    """紅茶メニュー表示"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE category = 'tea'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_tea.html', items=items)
    except Exception as e:
        return render_template('error.html', message=str(e))

@app.route('/menu/green_tea', methods=['GET'])
def menu_green_tea():
    """お茶メニュー表示"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE category = 'green_tea'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_green_tea.html', items=items)
    except Exception as e:
        return render_template('error.html', message=str(e))



@app.route('/menu/softdrink', methods=['GET'])
def menu_softdrink():
    """ソフトドリンクメニュー表示"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE category = 'softdrink'")
        items = cursor.fetchall()
        cursor.close()
        return render_template('menu_softdrink.html', items=items)
    except Exception as e:
        return render_template('error.html', message=str(e))


# ==================== カート関連ルート ====================
@app.route('/cart', methods=['GET'])
def view_cart():
    """カート表示"""
    cart = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total_price=total_price)


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
                session.modified = True
                return redirect('/cart')
        
        # 商品情報を取得
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, price FROM items WHERE id = %s", (item_id,))
        product = cursor.fetchone()
        cursor.close()

        if not product:
            return jsonify({'success': False, 'message': '商品が見つかりません'}), 404


        session['cart'].append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity
        })
        session.modified = True
        
        return redirect(url_for('view_cart'))
    except Exception as e:
        return render_template('error.html', message=str(e))


@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    """カートから商品を削除"""
    try:
        item_id = request.form.get('item_id')
        
        if not item_id:
            return "商品IDがありません", 400

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
        return render_template('checkout.html', cart=cart, total_price=total_price)
    else:
        # POST: 精算情報を確認
        return redirect(url_for('payment_method'))


@app.route('/payment_method', methods=['GET'])
def payment_method():
    """決済方法選択"""
    cart = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('payment_method.html', total_price=total_price)


@app.route('/payment', methods=['POST'])
def payment():
    """決済処理（疑似）"""
    try:
        payment_method = request.form.get('payment_method')
        
        # ここで決済処理を実装（疑似処理）
        # 実装例：
        # - クレジットカード: カード情報の検証
        # - 電子マネー: サービスとの連携
        # - 銀行振込: 振込情報の生成
        session['payment_method'] = payment_method
        return redirect(url_for('payment_complete'))
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
        cursor = mysql.connection.cursor()
        
        # 注文テーブルに挿入
        cursor.execute("""
            INSERT INTO orders (total, payment_method, purchase_datetime)
            VALUES (%s, %s, %s)
        """, (total_price, payment_method, datetime.now()))
        
        order_id = cursor.lastrowid
        
        # 注文詳細テーブルに挿入
        for item in cart:
            cursor.execute("""
                INSERT INTO order_details (ordered_id, item_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['id'], item['quantity'], item['price']))
        
        mysql.connection.commit()
        cursor.close()
        
        # カートをクリア
        session.pop('cart', None)
        session.modified = True
        
        return redirect(url_for('payment_success'))
    except Exception as e:
        mysql.connection.rollback()
        return render_template('error.html', message=str(e))

@app.route('/payment/complete/success', methods=['GET'])
def payment_success():
    return render_template('payment_success.html')

# ==================== 管理者ログイン ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理者ログイン"""
    if request.method == 'GET':
        return render_template('admin/login.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT id, username FROM admins WHERE username = %s AND password = %s",
                (username, hash_password(password))
            )
            admin = cursor.fetchone()
            cursor.close()
            
            if admin:
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['username']
                session.modified = True
                return redirect(url_for('admin/dashboard'))
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
            cursor = mysql.connection.cursor()
            
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
            return render_template('admin/error.html', message=str(e))
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
            
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO items (name, category, price, description, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, category, price, description, datetime.now()))
            
            mysql.connection.commit()
            cursor.close()
            
            return redirect(url_for('admin_items'))
        except Exception as e:
            return render_template('admin/error.html', message=str(e))

@app.route('/admin/item_edit/<int:item_id>', methods=['GET', 'POST'])
@admin_login_required
@admin_only
def admin_item_edit(item_id):
    """商品編集"""
    try:
        if request.method == 'GET':
            cursor = mysql.connection.cursor()
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
            
            cursor = mysql.connection.cursor()
            cursor.execute("""
                UPDATE items SET name = %s, category = %s, price = %s, description = %s
                WHERE id = %s
            """, (name, category, price, description, item_id))
            
            mysql.connection.commit()
            cursor.close()
            
            return redirect(url_for('admin_items'))
    except Exception as e:
        return render_template('admin/error.html', message=str(e))

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
        
        return redirect(url_for('admin_items'))
    except Exception as e:
        return render_template('admin/error.html', message=str(e))

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
                
                return csv_data, 200, {'Content-Disposition': 'attachment; filename=items.csv'}
            except Exception as e:
                return render_template('admin/import_export.html', message=str(e))
        
        elif action == 'import':
            # インポート処理
            try:
                file = request.files.get('file')
                if file:
                    # CSVファイルを処理
                    # 実装例：
                    # - ファイルの検証
                    # - データベースに挿入
                    pass
                return redirect(url_for('admin_import_export'))
            except Exception as e:
                return render_template('admin/error.html', message=str(e))


# ==================== 管理者・購入履歴検索 ====================
@app.route('/admin/search_history', methods=['GET', 'POST'])
@admin_login_required
def admin_search_history():
    """購入履歴検索"""
    search = request.args.get('search', '')
    date = request.args.get('date', '')
        
    try:
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT 
                o.id AS id,
                o.total AS total,
                o.payment_method,
                o.purchase_datetime,
                d.item_id,
                d.name AS name,
                d.price AS price,
                d.quantity
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
        return render_template('admin/error.html', message=str(e))

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
            return render_template('admin/error.html', message=str(e))


# ==================== その他のルート ====================
@app.route('/logout', methods=['POST'])
def logout():
    """ログアウト"""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.modified = True
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラ"""
    return render_template('admin/error.html', message='ページが見つかりません'), 404


@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラ"""
    mysql.connection.rollback()
    return render_template('admin/error.html', message='サーバーエラーが発生しました'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
