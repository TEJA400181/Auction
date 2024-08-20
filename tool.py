from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(_name_)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction.db'
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Auction model
class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    starting_bid = db.Column(db.Float, nullable=False)
    current_bid = db.Column(db.Float, nullable=False)
    auctioneer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    bids = db.relationship('Bid', backref='auction', lazy=True)

# Bid model
class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    auction_id = db.Column(db.Integer, db.ForeignKey('auction.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='sha256')

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

# User dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    auctions = Auction.query.filter(Auction.end_time > datetime.utcnow()).all()
    return render_template('dashboard.html', auctions=auctions)

# Create an auction
@app.route('/create-auction', methods=['GET', 'POST'])
def create_auction():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        starting_bid = float(request.form['starting_bid'])
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%d %H:%M:%S')

        new_auction = Auction(
            title=title,
            description=description,
            starting_bid=starting_bid,
            current_bid=starting_bid,
            auctioneer_id=session['user_id'],
            end_time=end_time
        )
        db.session.add(new_auction)
        db.session.commit()

        flash('Auction created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_auction.html')

# Bid on an auction
@app.route('/bid/<int:auction_id>', methods=['POST'])
def bid(auction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    auction = Auction.query.get_or_404(auction_id)
    bid_amount = float(request.form['bid_amount'])

    if bid_amount > auction.current_bid:
        new_bid = Bid(
            amount=bid_amount,
            bidder_id=session['user_id'],
            auction_id=auction_id
        )
        auction.current_bid = bid_amount
        db.session.add(new_bid)
        db.session.commit()

        flash('Bid placed successfully!', 'success')
    else:
        flash('Bid amount must be higher than the current bid.', 'danger')

    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Run the app
if _name_ == '_main_':
    db.create_all()
    app.run(debug=True)
