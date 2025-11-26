import os
import io
import base64
from datetime import datetime

from flask import (
    Flask, session, render_template, request, 
    redirect, url_for, flash, jsonify, send_file
)
from flask_bcrypt import Bcrypt

from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode
import smtplib

import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from database import Base, Accounts, Customers, Users, CustomerLog, Transactions
from portfolio import PortfolioUser, WatchlistItem, Position
from portfolio.services.price_feed import PriceFeedService
from auth_logger import log_login_attempt, log_totp_verification, log_logout
from strategies import StrategyFactory

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

bcrypt = Bcrypt(app)

engine = create_engine(
    'sqlite:///database.db',
    connect_args={'check_same_thread': False},
    echo=False
)
Base.metadata.bind = engine
db = scoped_session(sessionmaker(bind=engine))

EMAIL_SENDER = 'paranthagan2311@gmail.com'
EMAIL_PASSWORD = 'lslobbmwfsjxajez'

price_feed = PriceFeedService()

def get_totp_db():
    
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_totp_db():
    
    conn = get_totp_db()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                totp_secret TEXT NOT NULL,
                role TEXT DEFAULT 'customer'
            )
        ''')
        
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' not in columns:
            try:
                conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'customer'")
                conn.execute("UPDATE users SET role = 'customer' WHERE role IS NULL")
                print("✓ Added 'role' column to users table")
            except Exception as e:
                print(f"Note: Could not add role column: {e}")
    conn.close()

def init_admin_user():
    
    admin_email = "admin@gmail.com"
    admin_user = db.query(Users).filter_by(id=admin_email).first()
    
    if not admin_user:
        admin_pass = "Admin@1234".encode('utf-8')
        hashed_password = bcrypt.generate_password_hash(admin_pass)
        new_admin = Users(
            id=admin_email,
            name="Administrator",
            user_type="ADMIN",
            password=hashed_password
        )
        try:
            db.add(new_admin)
            db.commit()
            print("✓ Admin user created successfully")
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating admin user: {e}")

def send_email(subject, message, recipient_email):
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        msg = f"Subject: {subject}\n\n{message}"
        server.sendmail(EMAIL_SENDER, recipient_email, msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def require_login(f):
    
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_customer(f):
    
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'customer':
            flash("Customer access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def welcome():
    
    return render_template("welcome.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'customer')

        if not all([username, email, password, role]):
            flash('All fields are required!', 'danger')
            return render_template('register.html')

        if role not in ['customer', 'admin']:
            flash('Invalid role selected!', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        totp_secret = pyotp.random_base32()

        conn = get_totp_db()
        user_exists = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if user_exists:
            conn.close()
            flash('Username or email already exists!', 'danger')
            return render_template('register.html')

        try:
            with conn:
                conn.execute(
                    "INSERT INTO users (username, password, email, totp_secret, role) VALUES (?, ?, ?, ?, ?)",
                    (username, hashed_password, email, totp_secret, role)
                )
            
            totp = pyotp.TOTP(totp_secret)
            qr_url = totp.provisioning_uri(username, issuer_name="FinancialApp")
            send_email(
                "Setup your Authenticator App",
                f"Welcome {username}!\n\nScan this QR code in Google/Microsoft Authenticator:\n{qr_url}",
                email
            )
            
            session['temp_username'] = username
            session['registration_complete'] = True
            
            flash("Registration successful! You can view your QR code or check your email.", "success")
            return redirect(url_for('registration_success'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/registration_success')
def registration_success():
    
    if 'registration_complete' not in session:
        return redirect(url_for('login'))
    
    username = session.get('temp_username')
    return render_template('registration_success.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if 'user' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not all([username, password]):
            flash("Username and password are required.", "danger")
            return render_template('login.html')

        conn = get_totp_db()
        totp_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if totp_user and check_password_hash(totp_user['password'], password):
            session.pop('temp_username', None)
            session.pop('registration_complete', None)
            
            session['username'] = username
            session['totp_verified'] = False
            try:
                session['role'] = totp_user['role'] if 'role' in totp_user.keys() else 'customer'
            except (KeyError, IndexError):
                session['role'] = 'customer'
            
            try:
                log_login_attempt(username, True, 'PASSWORD')
                session['login_timestamp'] = datetime.now().timestamp()
            except Exception:
                pass
            
            return redirect(url_for('verify_totp'))

        usern = username.upper()
        passw = password.encode('utf-8')
        result = db.query(Users).filter_by(id=usern).first()

        if result and bcrypt.check_password_hash(result.password, passw):
            session['user'] = usern
            session['namet'] = result.name
            session['usert'] = result.user_type
            session['role'] = 'admin' if result.user_type == 'ADMIN' else 'customer'
            session['totp_verified'] = True

            try:
                log_login_attempt(username, True, 'LEGACY')
                session['login_timestamp'] = datetime.now().timestamp()
            except Exception:
                pass

            if result.user_type == 'ADMIN':
                portfolio_user = db.query(PortfolioUser).filter_by(
                    email=username.lower()
                ).first()
                
                if not portfolio_user:
                    portfolio_user = PortfolioUser(
                        name=result.name,
                        email=username.lower(),
                        risk_profile="Medium"
                    )
                    db.add(portfolio_user)
                    db.commit()

                session['portfolio_user_id'] = portfolio_user.id
                flash("Welcome to Admin Dashboard!", "success")
                return redirect(url_for('admin_dashboard'))

            flash(f"Welcome back, {result.name}!", "success")
            return redirect(url_for('customer_dashboard'))

        try:
            if totp_user or result:
                reason = 'invalid_password'
            else:
                reason = 'user_not_found'
            log_login_attempt(username, False, 'PASSWORD', reason)
        except Exception:
            pass

        flash("Invalid username or password.", "danger")

    return render_template('login.html')

@app.route('/verify_totp', methods=['GET', 'POST'])
def verify_totp():
    
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        entered_totp = request.form.get('totp', '').strip()
        username = session.get('username')

        conn = get_totp_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user:
            totp = pyotp.TOTP(user['totp_secret'])
            if totp.verify(entered_totp):
                session['user'] = username
                session['totp_verified'] = True
                session['namet'] = username
                try:
                    user_role = user['role'] if 'role' in user.keys() else 'customer'
                except (KeyError, IndexError):
                    user_role = 'customer'
                session['role'] = user_role
                
                try:
                    log_totp_verification(username, True)
                    session['login_timestamp'] = datetime.now().timestamp()
                except Exception:
                    pass
                
                flash(f"Welcome, {username}!", "success")
                
                if user_role == 'admin':
                    portfolio_user = db.query(PortfolioUser).filter_by(
                        email=user['email']
                    ).first()
                    
                    if not portfolio_user:
                        portfolio_user = PortfolioUser(
                            name=username,
                            email=user['email'],
                            risk_profile="Medium"
                        )
                        db.add(portfolio_user)
                        db.commit()
                    
                    session['portfolio_user_id'] = portfolio_user.id
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('customer_dashboard'))
            else:
                try:
                    log_totp_verification(username, False)
                except Exception:
                    pass
                
                flash('Invalid TOTP code. Please try again.', 'danger')

    return render_template('verify_totp.html')

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        conn = get_totp_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            new_totp_secret = pyotp.random_base32()
            conn.execute(
                "UPDATE users SET totp_secret = ? WHERE email = ?",
                (new_totp_secret, email)
            )
            conn.commit()
            conn.close()

            totp = pyotp.TOTP(new_totp_secret)
            qr_url = totp.provisioning_uri(user['username'], issuer_name="FinancialApp")
            send_email(
                "TOTP Recovery",
                f"Your TOTP has been reset.\n\nScan this QR code:\n{qr_url}",
                email
            )
            flash("Recovery email sent! Check your inbox.", "success")
            return redirect(url_for('login'))
        else:
            conn.close()
            flash('Email not found.', 'danger')

    return render_template('recover.html')

@app.route('/logout')
def logout():
    
    try:
        username = session.get('user') or session.get('username') or session.get('namet')
        login_timestamp = session.get('login_timestamp')
        
        if username:
            session_duration = None
            if login_timestamp:
                try:
                    session_duration = datetime.now().timestamp() - login_timestamp
                except Exception:
                    pass
            
            log_logout(username, session_duration)
    except Exception:
        pass
    
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route('/customer/dashboard')
@require_customer
def customer_dashboard():
    
    username = session.get('namet', session.get('user', 'User'))
    return render_template('home.html', username=username, role='customer')

@app.route('/financial_simulator')
@require_login
def financial_simulator():
    
    username = session.get('namet', session.get('user', 'User'))
    return render_template('financial_simulator.html', username=username)

@app.route('/api/investment-strategies')
@require_login
def get_investment_strategies():
    
    try:
        strategies = StrategyFactory.get_available_strategies()
        return jsonify({
            'success': True,
            'strategies': strategies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/investment-recommendation', methods=['POST'])
@require_login
def get_investment_recommendation():
    
    try:
        data = request.get_json()
        
        risk_profile = data.get('risk_profile', 'Medium')
        initial_savings = float(data.get('initial_savings', 0))
        monthly_contribution = float(data.get('monthly_contribution', 0))
        years = int(data.get('years', 10))
        
        strategy = StrategyFactory.create_strategy(risk_profile)
        
        allocation = strategy.get_asset_allocation()
        expected_return = strategy.get_expected_return()
        risk_level = strategy.get_risk_level()
        recommendations = strategy.get_recommendations()
        rebalancing_threshold = strategy.get_rebalancing_threshold()
        
        projection = strategy.calculate_projection(
            initial_savings, 
            monthly_contribution, 
            years
        )
        
        return jsonify({
            'success': True,
            'strategy': {
                'risk_profile': risk_profile,
                'risk_level': risk_level,
                'expected_return': expected_return,
                'asset_allocation': allocation,
                'rebalancing_threshold': rebalancing_threshold,
                'recommendations': recommendations
            },
            'projection': projection
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user-risk-profile')
@require_login
def get_user_risk_profile():
    
    try:
        user_email = session.get('user', '').lower()
        portfolio_user = db.query(PortfolioUser).filter_by(email=user_email).first()
        
        if portfolio_user:
            return jsonify({
                'success': True,
                'risk_profile': portfolio_user.risk_profile,
                'has_profile': True
            })
        else:
            return jsonify({
                'success': True,
                'risk_profile': 'Medium',
                'has_profile': False
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'risk_profile': 'Medium',
            'has_profile': False
        }), 500

@app.route('/fin_chatbot')
@require_login
def fin_chatbot():
    
    username = session.get('namet', session.get('user', 'User'))
    return render_template('fin_chatbot.html', username=username)

@app.route('/finhelp')
@require_login
def finhelp():
    
    username = session.get('namet', session.get('user', 'User'))
    return render_template('finhelp.html', username=username)

@app.route('/finhelp/upload', methods=['POST'])
@require_login
def finhelp_upload():
    
    if 'file' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('finhelp'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('finhelp'))
    
    if file:
        import os
        upload_folder = 'uploads'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        filename = f"user_{session.get('user', 'temp')}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        session['uploaded_file'] = filepath
        
        flash('File uploaded successfully! Analyzing...', 'success')
        return redirect(url_for('finhelp'))
    
    flash('Error uploading file', 'danger')
    return redirect(url_for('finhelp'))

@app.route('/finhelp/data')
@require_login
def finhelp_data():
    
    try:
        csv_path = session.get('uploaded_file', None)
        
        if os.path.exists(csv_path):
            import csv
            
            total_income = 0.0
            total_expense = 0.0
            recent = []
            category_totals = {}
            monthly_by_year = {}
            years = set()

            with open(csv_path, newline='', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                
                for i, row in enumerate(reader):
                    try:
                        label = (row.get('Expense/Income') or '').strip()
                        amt_raw = row.get('Amount (EUR)') or row.get('Amount') or '0'
                        amt = float(amt_raw) if amt_raw else 0.0
                    except Exception:
                        amt = 0.0

                    dt = None
                    try:
                        dt = datetime.fromisoformat(row.get('Date'))
                    except Exception:
                        try:
                            dt = datetime.strptime(row.get('Date'), '%Y-%m-%d')
                        except Exception:
                            pass

                    year = dt.year if dt else 'unknown'
                    years.add(year)
                    month_num = dt.month if dt else None
                    category = (row.get('Category') or '').strip() or (row.get('Name / Description') or '').strip()

                    category_totals.setdefault(year, {}).setdefault(label, {})
                    monthly_by_year.setdefault(year, {}).setdefault(label, {})
                    
                    category_totals[year][label][category] = category_totals[year][label].get(category, 0.0) + amt
                    
                    if month_num:
                        monthly_by_year[year][label][month_num] = monthly_by_year[year][label].get(month_num, 0.0) + amt

                    if label.lower() == 'income':
                        total_income += amt
                    elif label.lower() == 'expense':
                        total_expense += amt

                    signed_amt = amt if label.lower() == 'income' else -amt if label.lower() == 'expense' else amt
                    recent.append({
                        'id': i + 1,
                        'acc_id': None,
                        'message': row.get('Name / Description') or row.get('Transaction') or row.get('Category'),
                        'amount': signed_amt,
                        'time_stamp': dt.isoformat() if dt else None
                    })

            monthly_struct = {}
            for y in sorted(years, reverse=True):
                monthly_struct[y] = {}
                for label in monthly_by_year.get(y, {}):
                    arr = []
                    for mnum in sorted(monthly_by_year[y][label].keys()):
                        try:
                            mname = datetime(year=int(y) if y != 'unknown' else 2023, month=mnum, day=1).strftime('%b')
                        except Exception:
                            mname = str(mnum)
                        arr.append({'month': mnum, 'month_name': mname, 'total': monthly_by_year[y][label][mnum]})
                    monthly_struct[y][label] = arr

            category_struct = {}
            for y in sorted(years, reverse=True):
                category_struct[y] = {}
                for label in category_totals.get(y, {}):
                    arr = [
                        {'category': c, 'total': category_totals[y][label][c]}
                        for c in sorted(category_totals[y][label].keys(), key=lambda x: category_totals[y][label][x], reverse=True)
                    ]
                    category_struct[y][label] = arr

            return jsonify({
                'total_income': total_income,
                'total_expense': total_expense,
                'recent': recent[:50],
                'monthly_by_year': monthly_struct,
                'category_by_year': category_struct,
                'years': sorted([y for y in years if y != 'unknown'], reverse=True)
            })

        txs = db.query(Transactions).order_by(Transactions.time_stamp.desc()).limit(100).all()
        total_income = 0.0
        total_expense = 0.0
        monthly = {}
        recent = []

        for t in txs:
            amt = t.amount or 0
            ts = t.time_stamp
            month = ts.strftime('%Y-%m') if ts else 'unknown'
            monthly.setdefault(month, 0)
            monthly[month] += amt

            if amt >= 0:
                total_income += amt
            else:
                total_expense += abs(amt)

            recent.append({
                'id': t.trans_id,
                'acc_id': t.acc_id,
                'message': t.trans_message,
                'amount': amt,
                'time_stamp': ts.isoformat() if ts else None
            })

        monthly_list = [{'month': m, 'total': monthly[m]} for m in sorted(monthly.keys(), reverse=True)]

        return jsonify({
            'total_income': total_income,
            'total_expense': total_expense,
            'monthly': monthly_list,
            'recent': recent
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    
    portfolio_user = db.query(PortfolioUser).filter_by(
        id=session.get('portfolio_user_id')
    ).first()
    
    if not portfolio_user:
        flash("Portfolio not found.", "danger")
        return redirect(url_for('login'))

    positions = db.query(Position).filter_by(user_id=portfolio_user.id).all()
    watchlist = db.query(WatchlistItem).filter_by(user_id=portfolio_user.id).all()

    # Update price feed
    symbols = set([p.symbol for p in positions] + [w.symbol for w in watchlist])
    if symbols:
        price_feed.add_symbols(list(symbols))
        if not price_feed.running:
            price_feed.start()

    prices = price_feed.get_prices()
    total_value = sum([p.quantity * prices.get(p.symbol, {}).get('price', p.avg_cost) for p in positions])
    total_cost = sum([p.quantity * p.avg_cost for p in positions])
    total_gain = total_value - total_cost

    return render_template(
        'portfolio/dashboard.html',
        user=portfolio_user,
        positions=positions,
        watchlist=watchlist,
        prices=prices,
        total_value=total_value,
        total_cost=total_cost,
        total_gain=total_gain,
        username=session.get('namet', session.get('user', 'Admin'))
    )

@app.route('/portfolio/watchlist')
@require_admin
def portfolio_watchlist():
    
    portfolio_user = db.query(PortfolioUser).filter_by(
        id=session.get('portfolio_user_id')
    ).first()
    watchlist = db.query(WatchlistItem).filter_by(user_id=portfolio_user.id).all()

    symbols = [item.symbol for item in watchlist]
    if symbols:
        price_feed.add_symbols(symbols)
        if not price_feed.running:
            price_feed.start()

    prices = price_feed.get_prices()
    return render_template('portfolio/watchlist.html', watchlist=watchlist, user=portfolio_user, prices=prices)

@app.route('/portfolio/watchlist/add', methods=['POST'])
@require_admin
def portfolio_watchlist_add():
    
    symbol = request.form.get('symbol', '').strip().upper()
    
    if not symbol:
        flash("Symbol is required.", "danger")
        return redirect(url_for('portfolio_watchlist'))

    try:
        watchlist_item = WatchlistItem(
            user_id=session.get('portfolio_user_id'),
            symbol=symbol
        )
        db.add(watchlist_item)
        db.commit()
        flash(f"Added {symbol} to watchlist.", "success")
    except Exception:
        db.rollback()
        flash("Symbol already in watchlist or invalid.", "danger")

    return redirect(url_for('portfolio_watchlist'))

@app.route('/portfolio/watchlist/remove', methods=['POST'])
@require_admin
def portfolio_watchlist_remove():
    
    symbol = request.form.get('symbol', '').strip().upper()
    
    if not symbol:
        flash("Symbol is required.", "danger")
        return redirect(url_for('portfolio_watchlist'))

    try:
        item = db.query(WatchlistItem).filter_by(
            user_id=session.get('portfolio_user_id'),
            symbol=symbol
        ).first()
        
        if item:
            db.delete(item)
            db.commit()
            flash(f"Removed {symbol} from watchlist.", "success")
        else:
            flash("Symbol not found in watchlist.", "danger")
    except Exception:
        db.rollback()
        flash("Error removing from watchlist.", "danger")

    return redirect(url_for('portfolio_watchlist'))

@app.route('/portfolio/positions')
@require_admin
def portfolio_positions():
    
    portfolio_user = db.query(PortfolioUser).filter_by(
        id=session.get('portfolio_user_id')
    ).first()
    positions = db.query(Position).filter_by(user_id=portfolio_user.id).all()

    symbols = [position.symbol for position in positions]
    if symbols:
        price_feed.add_symbols(symbols)
        if not price_feed.running:
            price_feed.start()

    prices = price_feed.get_prices()
    return render_template('portfolio/positions.html', positions=positions, user=portfolio_user, prices=prices)

@app.route('/portfolio/positions/add', methods=['POST'])
@require_admin
def portfolio_positions_add():
    
    symbol = request.form.get('symbol', '').strip().upper()
    quantity = request.form.get('quantity', '')
    avg_cost = request.form.get('avg_cost', '')

    if not all([symbol, quantity, avg_cost]):
        flash("All fields are required.", "danger")
        return redirect(url_for('portfolio_positions'))

    try:
        quantity = float(quantity)
        avg_cost = float(avg_cost)

        position = Position(
            user_id=session.get('portfolio_user_id'),
            symbol=symbol,
            quantity=quantity,
            avg_cost=avg_cost
        )
        db.add(position)
        db.commit()
        flash(f"Added position in {symbol}.", "success")
    except ValueError:
        flash("Invalid quantity or average cost.", "danger")
    except Exception:
        db.rollback()
        flash("Symbol already in portfolio or invalid.", "danger")

    return redirect(url_for('portfolio_positions'))

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.route('/generate_qr_code')
def generate_qr_code():
    
    # Check if user is in registration, TOTP verification, or already logged in
    username = session.get('temp_username') or session.get('username') or session.get('user')
    
    if not username:
        flash("Please login or register first.", "warning")
        return redirect(url_for('login'))

    conn = get_totp_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if user:
        secret = user['totp_secret']
        totp_link = f'otpauth://totp/FinancialApp:{username}?secret={secret}&issuer=FinancialApp'
        qr = qrcode.make(totp_link)

        buffer = io.BytesIO()
        qr.save(buffer, format='PNG')
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()

        return render_template('qr_code.html', qr_code_image=qr_code_image)
    else:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

@app.route('/delete_db', methods=['GET', 'POST'])
@require_admin
def delete_db():
    
    if request.method == 'POST':
        if os.path.exists('users.db'):
            os.remove('users.db')
            flash("TOTP Database deleted successfully!", "success")
            init_totp_db()
        else:
            flash("Database does not exist!", "warning")
        return redirect(url_for('admin_dashboard'))

    return render_template('delete_db.html')

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    
    return render_template('404.html'), 500

# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    # Initialize databases
    init_totp_db()
    Base.metadata.create_all(engine)
    init_admin_user()
    
    # Run application
    print("=" * 60)
    print("Financial Services Dashboard")
    print("=" * 60)
    print("Server starting on http://0.0.0.0:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
