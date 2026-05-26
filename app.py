from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# MySQL設定
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'selfdrinkbar')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# ==================== ユーティリティ関数 ====================
def hash_password(password):
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()


def admin_login_required(f):
    """管理者ログイン確認デコレータ"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ==================== メニュー関連ルート ====================
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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': str(e)}), 500


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
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        if 'cart' not in session:
            session['cart'] = []
        
        # 既存のカート内容から商品を検索
        for item in session['cart']:
            if item['id'] == item_id:
                item['quantity'] += quantity
                session.modified = True
                return jsonify({'success': True, 'message': '商品数量を更新しました'})
        
        # 商品情報を取得
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, price FROM items WHERE id = %s", (item_id,))
        product = cursor.fetchone()
        cursor.close()
        
        if product:
            session['cart'].append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity
            })
            session.modified = True
            return jsonify({'success': True, 'message': '商品をカートに追加しました'})
        
        return jsonify({'success': False, 'message': '商品が見つかりません'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    """カートから商品を削除"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        if 'cart' in session:
            session['cart'] = [item for item in session['cart'] if item['id'] != item_id]
            session.modified = True
            return jsonify({'success': True, 'message': '商品をカートから削除しました'})
        
        return jsonify({'success': False, 'message': 'カートが空です'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        data = request.get_json()
        payment_method = data.get('payment_method')
        
        # ここで決済処理を実装（疑似処理）
        # 実装例：
        # - クレジットカード: カード情報の検証
        # - 電子マネー: サービスとの連携
        # - 銀行振込: 振込情報の生成
        
        return jsonify({'success': True, 'message': '決済処理が完了しました'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/payment/complete', methods=['POST'])
def payment_complete():
    """決済完了"""
    try:
        data = request.get_json()
        cart = session.get('cart', [])
        total_price = data.get('total_price')
        payment_method = data.get('payment_method')
        
        # 購入履歴をDBに保存
        cursor = mysql.connection.cursor()
        
        # 注文テーブルに挿入
        cursor.execute("""
            INSERT INTO orders (user_id, total_price, payment_method, created_at)
            VALUES (%s, %s, %s, %s)
        """, (session.get('user_id'), total_price, payment_method, datetime.now()))
        
        order_id = cursor.lastrowid
        
        # 注文詳細テーブルに挿入
        for item in cart:
            cursor.execute("""
                INSERT INTO order_details (order_id, item_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['id'], item['quantity'], item['price']))
        
        mysql.connection.commit()
        cursor.close()
        
        # カートをクリア
        session.pop('cart', None)
        session.modified = True
        
        return jsonify({'success': True, 'order_id': order_id, 'message': '決済が完了しました'})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 管理者ログイン ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理者ログイン"""
    if request.method == 'GET':
        return render_template('admin_login.html')
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
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('admin_login.html', error='ユーザー名またはパスワードが間違っています')
        except Exception as e:
            return render_template('admin_login.html', error=str(e))


# ==================== 管理者ダッシュボード ====================
@app.route('/admin/dashboard', methods=['GET'])
@admin_login_required
def admin_dashboard():
    """管理者メニュー"""
    return render_template('admin_dashboard.html')


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
            
            return render_template('admin_items.html', items=items)
        except Exception as e:
            return render_template('admin_items.html', error=str(e))
    else:
        # POST: 検索実行
        return redirect(url_for('admin_items', 
                               search=request.form.get('search'),
                               category=request.form.get('category')))


@app.route('/admin/register', methods=['GET', 'POST'])
@admin_login_required
def admin_register():
    """商品登録"""
    if request.method == 'GET':
        return render_template('admin_register.html')
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
            return render_template('admin_register.html', error=str(e))


@app.route('/admin/item_edit/<int:item_id>', methods=['GET', 'POST'])
@admin_login_required
def admin_item_edit(item_id):
    """商品編集"""
    try:
        if request.method == 'GET':
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            cursor.close()
            
            if not item:
                return render_template('error.html', message='商品が見つかりません'), 404
            
            return render_template('admin_item_edit.html', item=item)
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
        return render_template('error.html', message=str(e))


@app.route('/admin/item_delete', methods=['POST'])
@admin_login_required
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
        return render_template('error.html', message=str(e))


# ==================== 管理者・CSVインポート/エクスポート ====================
@app.route('/admin/import_export', methods=['GET', 'POST'])
@admin_login_required
def admin_import_export():
    """CSVインポート/エクスポート"""
    if request.method == 'GET':
        return render_template('admin_import_export.html')
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
                return render_template('admin_import_export.html', error=str(e))
        
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
                return render_template('admin_import_export.html', error=str(e))


# ==================== 管理者・購入履歴検索 ====================
@app.route('/admin/search_history', methods=['GET', 'POST'])
@admin_login_required
def admin_search_history():
    """購入履歴検索"""
    if request.method == 'GET':
        search_keyword = request.args.get('search', '')
        
        try:
            cursor = mysql.connection.cursor()
            
            query = "SELECT * FROM orders WHERE 1=1"
            params = []
            
            if search_keyword:
                query += " AND (id LIKE %s OR user_id LIKE %s)"
                params.extend([f"%{search_keyword}%", f"%{search_keyword}%"])
            
            cursor.execute(query, params)
            orders = cursor.fetchall()
            cursor.close()
            
            return render_template('admin_search_history.html', orders=orders)
        except Exception as e:
            return render_template('admin_search_history.html', error=str(e))
    else:
        return redirect(url_for('admin_search_history', search=request.form.get('search')))


# ==================== 管理者・パスワード変更 ====================
@app.route('/admin/password', methods=['GET', 'POST'])
@admin_login_required
def admin_password():
    """パスワード変更"""
    if request.method == 'GET':
        return render_template('admin_password.html')
    else:
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                return render_template('admin_password.html', error='新しいパスワードが一致しません')
            
            admin_id = session.get('admin_id')
            
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT password FROM admins WHERE id = %s", (admin_id,))
            admin = cursor.fetchone()
            
            if not admin or admin['password'] != hash_password(current_password):
                cursor.close()
                return render_template('admin_password.html', error='現在のパスワードが正しくありません')
            
            cursor.execute(
                "UPDATE admins SET password = %s WHERE id = %s",
                (hash_password(new_password), admin_id)
            )
            
            mysql.connection.commit()
            cursor.close()
            
            return render_template('admin_password.html', message='パスワードを変更しました')
        except Exception as e:
            return render_template('admin_password.html', error=str(e))


# ==================== その他のルート ====================
@app.route('/')
def index():
    """ホームページ"""
    return render_template('index.html')


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
    return render_template('error.html', message='ページが見つかりません'), 404


@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラ"""
    mysql.connection.rollback()
    return render_template('error.html', message='サーバーエラーが発生しました'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
