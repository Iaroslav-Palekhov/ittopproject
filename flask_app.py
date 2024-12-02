import hashlib
import json
import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'
data_file = 'data.json'

def read_data():
    if not os.path.exists(data_file):
        return {'users': [], 'products': []}
    with open(data_file, 'r') as f:
        return json.load(f)

def write_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, user_password):
    return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('auth.html')


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_name = request.form['product_name']
    product_price = request.form['product_price']
    cart = session.get('cart', [])

    # Добавляем товар в корзину
    cart.append({'name': product_name, 'price': product_price})
    session['cart'] = cart

    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = read_data()

        if any(user['username'] == username for user in data['users']):
            return render_template('register.html', error="Username already exists. Please choose a different one.")

        hashed_password = hash_password(password)
        new_user = {'username': username, 'password': hashed_password}
        data['users'].append(new_user)
        write_data(data)
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = read_data()
        user = next((user for user in data['users'] if user['username'] == username), None)

        if user and check_password(user['password'], password):
            session['user_id'] = user['username']
            return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    data = read_data()
    if request.method == 'POST':
        return add_product()

    products = data['products']
    return render_template('home.html', products=products)


@app.route('/add_product', methods=['POST'])
def add_product():
    data = read_data()
    try:
        product_name = request.form['product_name']
        product_price = float(request.form['product_price'])

        # Handle file upload
        product_image = request.files['product_image']
        if product_image:
            # Create a directory for uploaded images if it doesn't exist
            upload_folder = 'static/uploads'
            os.makedirs(upload_folder, exist_ok=True)

            # Save the file
            image_filename = product_image.filename
            image_path = os.path.join(upload_folder, image_filename)
            product_image.save(image_path)

            new_product = {'name': product_name, 'price': product_price, 'image_path': image_path}
            data['products'].append(new_product)
            write_data(data)

            return redirect(url_for('home'))
    except Exception as e:
        print(f"Error adding product: {e}")
        return f"An error occurred while adding the product: {e}", 500

@app.route('/add', methods=['GET'])
def add():
    data = read_data()
    products = data['products']
    return render_template('add.html', products=products)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    data = read_data()
    if 0 <= product_id < len(data['products']):
        del data['products'][product_id]
        write_data(data)
    return redirect(url_for('add'))

@app.route('/order')
def order():
    cart = session.get('cart', [])
    total = sum(float(item['price']) for item in cart)
    return render_template('order.html', cart=cart, total=total)



@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_name = request.form['product_name']
    cart = session.get('cart', [])
    cart = [item for item in cart if item['name'] != product_name]
    session['cart'] = cart
    return redirect(url_for('order'))

@app.route('/profile')
def profile():
    username = session.get('user_id', "Гость")
    return render_template('profile.html', username=username)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/zakazi')
def zakazi():
    return render_template('zakazi.html')


@app.route('/ofer', methods=['POST'])
def ofer():
    cart = session.get('cart', [])
    if not cart:
        return "Корзина пуста", 400

    data = read_data()


    if 'orders' not in data:
        data['orders'] = []

    order = {
        'username': session.get('user_id', 'Гость'),
        'items': cart,
        'total': sum(float(item['price']) for item in cart)
    }

    data['orders'].append(order)
    write_data(data)

    session['cart'] = []

    return render_template('ofer.html', message="Заказ оформлен!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4500, debug=True)