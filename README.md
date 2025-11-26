# Financial Services Dashboard - Complete Setup Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [User Roles](#user-roles)
4. [Features](#features)
5. [Usage Guide](#usage-guide)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Start the Application
```bash
cd fsdNew
python app.py
```

Access at: **http://localhost:5000**

### Quick Admin Login (No TOTP)
```
Username: ADMIN@GMAIL.COM
Password: adminpass
```
→ Direct access to Portfolio Analyzer

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Install Dependencies
```bash
pip install -r requirements_portfolio.txt
```

### Required Packages
- Flask
- Flask-Bcrypt
- SQLAlchemy
- PyOTP
- qrcode
- yfinance (optional, for real stock prices)
- Werkzeug

---

## 👥 User Roles

### Customer Role
**Access**: Financial management tools
- Fin Chatbot
- Financial Simulator
- Financial Summarizer

### Admin Role
**Access**: All customer features + Portfolio Analyzer
- Portfolio Dashboard
- Stock Positions Management
- Watchlist Management
- Real-time Price Tracking

---

## 🎯 Features

### 1. 💬 Fin Chatbot
- AI-powered financial assistant
- 24/7 instant advice
- Financial questions and answers

### 2. 📊 Financial Simulator
- Scenario modeling
- Savings projections
- Investment return calculations
- Time-based analysis

### 3. 📋 Financial Summarizer (NEW!)
**Upload & Analyze Your Financial Documents**

#### Supported Formats:
- CSV files (.csv)
- Excel files (.xlsx, .xls)
- Text files (.txt)

#### Expected Data Format:
- Transaction Date
- Description/Name
- Amount
- Category (optional)

#### Features:
- Drag & drop file upload
- Automatic analysis
- Income vs Expense breakdown
- Monthly trends
- Category-wise spending
- Visual charts and graphs

### 4. 📈 Portfolio Analyzer (Admin Only)
- Real-time stock prices
- Position tracking
- Gain/Loss calculations
- Watchlist management
- Portfolio analytics

---

## 📖 Usage Guide

### Registration (Customer or Admin)

#### Step 1: Register
1. Go to http://localhost:5000/register
2. **Select Role**:
   - 👤 Customer: Personal financial tools
   - 👨‍💼 Admin: Portfolio management
3. Fill in details:
   - Username (3-50 characters)
   - Email (valid format)
   - Password (min 8 chars, uppercase, lowercase, numbers)
4. Click "Create Account"

#### Step 2: TOTP Setup
After registration:
- **Option A**: Click "View QR Code Now" → Scan with authenticator app
- **Option B**: Check email → Scan QR code from email

#### Step 3: Login
1. Enter username and password
2. Enter 6-digit TOTP code from authenticator app
3. Access your dashboard

### Using Financial Summarizer

#### Upload Your File
1. Go to Financial Summarizer
2. Click "Choose File" or drag & drop
3. Select your financial document (CSV, Excel, or Text)
4. Click "Analyze Document"

#### View Results
- Total Income/Expense/Balance
- Expense breakdown (pie chart)
- Monthly trends (bar chart)
- Recent transactions table

#### Upload Another File
- Click "Upload Another File" to analyze different data

### Managing Portfolio (Admin)

#### Add Position
1. Go to Portfolio → Positions
2. Enter:
   - Stock Symbol (e.g., AAPL)
   - Quantity
   - Average Cost
3. Click "Add Position"

#### Add to Watchlist
1. Go to Portfolio → Watchlist
2. Enter stock symbol
3. Click "Add to Watchlist"

#### View Dashboard
- Portfolio overview
- Total value and gains
- Position summary
- Watchlist preview

---

## 🔐 Security Features

### Authentication
- Password hashing with Bcrypt
- TOTP Two-Factor Authentication
- Session-based authentication
- Role-based access control

### Data Protection
- Input validation and sanitization
- XSS protection
- CSRF protection
- Secure file uploads

---

## 🗂️ File Structure

```
fsdNew/
├── app.py                      # Main application
├── database.py                 # Database models
├── requirements_portfolio.txt  # Dependencies
├── .gitignore                  # Git ignore rules
├── database.db                 # Main database
├── users.db                    # TOTP users database
├── uploads/                    # Uploaded files (auto-created)
├── portfolio/                  # Portfolio module
│   ├── __init__.py
│   └── services/
│       └── price_feed.py
├── static/
│   ├── css/
│   │   └── main.css
│   ├── js/
│   │   └── main.js
│   └── logo1.png
└── templates/
    ├── welcome.html
    ├── login.html
    ├── register.html
    ├── registration_success.html
    ├── verify_totp.html
    ├── qr_code.html
    ├── recover.html
    ├── home.html
    ├── fin_chatbot.html
    ├── financial_simulator.html
    ├── finhelp.html
    ├── delete_db.html
    ├── 404.html
    └── portfolio/
        ├── dashboard.html
        ├── positions.html
        └── watchlist.html
```

---

## 🐛 Troubleshooting

### Issue: Port 5000 already in use
**Solution**: Change port in app.py:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Issue: Database not found
**Solution**: Delete and restart:
```bash
del database.db users.db
python app.py
```

### Issue: TOTP not working
**Solution**:
1. Ensure phone time is synchronized
2. Click "Show QR Code" during verification
3. Re-scan with authenticator app
4. Use "Lost Access?" to reset

### Issue: File upload not working
**Solution**:
1. Check file format (CSV, Excel, Text)
2. Ensure file has proper structure
3. Check file size (< 10MB recommended)
4. Verify uploads folder permissions

### Issue: Styles not loading
**Solution**: Clear browser cache (Ctrl+Shift+Delete)

---

## 📊 Default Credentials

### Legacy Admin (No TOTP)
```
Username: ADMIN@GMAIL.COM
Password: adminpass
Access: Full admin + portfolio features
```

---

## 🎨 Design Features

- Clean white background
- Modern card-based layout
- Responsive design (mobile-friendly)
- Smooth animations
- Real-time form validation
- Auto-dismissing alerts
- Professional typography

---

## 📱 Browser Support

### Recommended Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Mobile Support
- iOS Safari
- Chrome Mobile
- Samsung Internet

---

## 🔧 Configuration

### Email Settings
Edit in `app.py`:
```python
EMAIL_SENDER = 'your-email@gmail.com'
EMAIL_PASSWORD = 'your-app-password'
```

### Database Location
- `database.db` - Main banking database
- `users.db` - TOTP users database
- `uploads/` - Uploaded financial documents

### Debug Mode
For production, set in `app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

---

## 📈 Tips & Best Practices

### For Customers
1. Upload CSV files with clear transaction data
2. Include date, description, and amount columns
3. Use consistent date formats
4. Categorize transactions for better insights

### For Admins
1. Add positions with accurate cost basis
2. Track multiple symbols in watchlist
3. Review portfolio regularly
4. Monitor real-time price updates

### Security
1. Use strong passwords (8+ chars, mixed case, numbers)
2. Keep TOTP app secure
3. Don't share admin credentials
4. Logout after each session

---

## 🆘 Support

### Common Commands

#### Check Application Status
```bash
python app.py
```

#### Install/Update Dependencies
```bash
pip install -r requirements_portfolio.txt --upgrade
```

#### Clear Uploaded Files
```bash
# Windows
rmdir /s /q uploads

# Linux/Mac
rm -rf uploads
```

---

## ✅ Feature Checklist

### Customer Features
- ✅ Fin Chatbot
- ✅ Financial Simulator
- ✅ Financial Summarizer (with file upload)
- ✅ TOTP Authentication
- ✅ Session Management

### Admin Features
- ✅ All Customer Features
- ✅ Portfolio Dashboard
- ✅ Position Management
- ✅ Watchlist Management
- ✅ Real-time Prices
- ✅ Gain/Loss Tracking

### Security
- ✅ Password Hashing
- ✅ TOTP 2FA
- ✅ Input Validation
- ✅ XSS Protection
- ✅ CSRF Protection
- ✅ Role-Based Access

---

## 🎉 Quick Reference

### URLs
- Home: http://localhost:5000
- Login: http://localhost:5000/login
- Register: http://localhost:5000/register
- Customer Dashboard: http://localhost:5000/customer/dashboard
- Admin Dashboard: http://localhost:5000/admin/dashboard

### File Upload Formats
- CSV: `.csv`
- Excel: `.xlsx`, `.xls`
- Text: `.txt`

### Authenticator Apps
- Google Authenticator
- Microsoft Authenticator
- Authy
- Any TOTP-compatible app

---

## 📞 Need Help?

1. Check this guide first
2. Review error messages in terminal
3. Check browser console (F12)
4. Verify file formats and data structure
5. Ensure all dependencies are installed

---

**Version**: 4.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: 2025

---

## 🎯 Summary

This application provides:
- **Customer Tools**: Chatbot, Simulator, Summarizer (with file upload)
- **Admin Tools**: Portfolio Analyzer with real-time tracking
- **Security**: TOTP 2FA, password hashing, role-based access
- **Modern UI**: Clean, responsive, professional design
- **File Analysis**: Upload and analyze financial documents

**Ready to use!** Start with `python app.py` and access at http://localhost:5000
