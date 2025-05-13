from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eb2d8cffa798f7374307385e85e3fd809de946ac7c34df4745f2a22d6c585716'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    total_amount = db.Column(db.Float, default=0.0)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_time = db.Column(db.Float, nullable=False)
    menu_item = db.relationship('MenuItem')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.created_at.desc()).all()
    menu_items = MenuItem.query.all()
    return render_template('dashboard.html', orders=orders, menu_items=menu_items)

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.get_json()
    table_number = data.get('table_number')
    customer_name = data.get('customer_name')
    items = data.get('items')
    
    if not items:
        return jsonify({'error': 'No items in order'}), 400
    
    order = Order(table_number=table_number, customer_name=customer_name)
    total_amount = 0
    
    for item in items:
        menu_item = MenuItem.query.get(item['id'])
        if not menu_item or menu_item.stock < item['quantity']:
            return jsonify({'error': 'Not enough stock for {}'.format(menu_item.name)}), 400
        
        order_item = OrderItem(
            menu_item_id=item['id'],
            quantity=item['quantity'],
            price_at_time=menu_item.price
        )
        order.items.append(order_item)
        menu_item.stock -= item['quantity']
        total_amount += menu_item.price * item['quantity']
    
    order.total_amount = total_amount
    db.session.add(order)
    db.session.commit()
    
    return jsonify({'message': 'Order placed successfully', 'order_id': order.id})

@app.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    order = Order.query.get_or_404(order_id)
    status = request.json.get('status')
    
    if status not in ['pending', 'preparing', 'ready', 'delivered']:
        return jsonify({'error': 'Invalid status'}), 400
    
    order.status = status
    db.session.commit()
    return jsonify({'message': 'Order status updated'})

@app.route('/restock', methods=['POST'])
@login_required
def restock():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    menu_item = MenuItem.query.get(data['id'])
    if not menu_item:
        return jsonify({'error': 'Item not found'}), 404
    
    menu_item.stock += data['quantity']
    db.session.commit()
    return jsonify({'message': 'Stock updated successfully'})

@app.route('/get_orders')
def get_orders():
    orders = Order.query.filter(Order.status=='pending').order_by(Order.created_at.desc()).all()
    return jsonify([{
        'table_number': order.table_number,
        'customer_name': order.customer_name,
        'status': order.status
    } for order in orders])

@app.route('/home')
@login_required
def home():
    menu_items = MenuItem.query.all()
    orders = Order.query.filter(Order.status=='pending').order_by(Order.created_at.desc()).all()
    return render_template('index.html', menu_items=menu_items, orders=orders)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 