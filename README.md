# 📚 Library Management System (LibManager)

A modern, full-featured **Library Management System** built with **Django**, featuring role-based access control, book cataloguing, borrowing requests, automated overdue fine calculation, and an integrated **online payment gateway & checkout system** with official receipt generation.

---

## 🚀 Key Features

### 1. 👥 Multi-Role User Authentication
- **Admin**: Complete system control, book inventory management, user management, financial tracking, and transaction oversight.
- **Librarian**: Book issue & return management, borrowing request approvals/rejections, and fine collection reporting.
- **Student**: Book catalogue browsing, one-click borrowing requests, active issue tracking, overdue notifications, online fine payments, and printable receipts.

### 2. 📖 Book & Request Management
- Book inventory tracking (`total_copies`, `available_copies`, category, author, ISBN, publisher, and covers).
- Student borrowing request pipeline (`pending`, `approved`, `rejected`).
- Approving a request automatically issues the book and decrements available inventory.
- One-click book return workflow that dynamically recalculates late fines and restores book availability.

### 3. ⏱️ Automated Fine Calculation Engine
- Automatically checks unreturned and late-returned books against their `due_date`.
- Configurable daily fine rate (e.g., `₹5.00` per overdue day) defined in `settings.py`.
- **Zero False Fines**: No fine is charged if a book is returned on or before its due date.
- Dynamic calculations ensure amounts update accurately without requiring manual input.

### 4. 💳 Online Payment Gateway & Built-In Simulator
- **Razorpay Standard Integration**: Ready for production/test Razorpay API credentials.
- **Interactive No-KYC Payment Simulator**: Includes a full-featured built-in payment gateway simulator supporting **UPI / QR Code (GPay, PhonePe, Paytm)**, **Credit/Debit Cards**, and **Net Banking** — allowing instant demonstration and testing without requiring merchant KYC or a PAN card.
- **Security First**: Payment amounts are verified server-side to prevent client-side tampering.
- **Double-Payment Prevention**: Once a fine is marked `PAID`, duplicate transactions are strictly prevented.

### 5. 📄 Printable Official Payment Receipts
- Instant generation of verified library payment receipts upon settlement.
- Clean printable formatting (`window.print()` with optimized `@media print` CSS) for direct PDF export or physical printing.
- Privacy-protected: Students can only access their own receipts.

### 6. 🎨 Premium Glassmorphic Dark UI
- Modern aesthetic styled with curated palettes: `#0d1f23` (Background), `#132e35` (Secondary), `#2d4a53` (Accent), `#69818d` (Highlight), and translucent blurred cards (`backdrop-filter: blur(20px)`).
- Responsive data tables, real-time search filters, status badges, and overdue alert banners.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14+, Django 6.x
- **Database**: SQLite (Development) / PostgreSQL / MySQL
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphism Design System), JavaScript
- **Payment Processing**: Razorpay Python SDK (`razorpay`) + Custom Gateway Simulator
- **UI Frameworks**: Bootstrap 5 (Base Utilities), Crispy Forms, Select2

---

## 📂 Project Structure

```text
library_management/
├── accounts/                  # User authentication, profiles, signals, roles
├── books/                     # Book models, categories, authors, catalogue views
├── dashboard/                 # Role-based dashboard views & summary analytics
├── library_management/        # Project settings, root URL configuration, WSGI
├── media/                     # Uploaded book cover images
├── static/
│   ├── css/                   # Glassmorphic stylesheets (fines.css, dashboard.css, etc.)
│   └── js/                    # Razorpay checkout & gateway simulation scripts
├── templates/
│   ├── base.html              # Core navigation layout & glassmorphic header
│   ├── accounts/              # Login & registration templates
│   ├── books/                 # Book catalogue, add book, edit book templates
│   ├── dashboard/             # Role-specific analytics dashboard
│   └── transactions/          # Fines, payments, receipt, issue, and return templates
├── transactions/              # IssueBook, BookRequest, Fine, Notification models & views
├── manage.py
├── requirements.txt
└── README.md
```

---

## ⚡ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/gi-sketch/library_management.git
cd library_management
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install django razorpay django-select2 django-crispy-forms crispy-bootstrap5
```

### 4. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create an Administrator Superuser
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to **`http://127.0.0.1:8000/`**.

---

## ⚙️ Configuration (`settings.py` / `.env`)

You can customize fine rates and payment credentials in `library_management/settings.py` or via environment variables:

```python
# Daily fine rate per overdue day
DAILY_FINE_RATE = Decimal(os.environ.get('DAILY_FINE_RATE', '5.00'))

# Razorpay API Credentials (optional for live keys; built-in simulator activates if omitted)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_your_key_id')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'your_key_secret')
```

---

## 🌐 Main URLs & Routing

| Endpoint | Permitted Role | Description |
| :--- | :--- | :--- |
| `/` | Public | Homepage & library features overview |
| `/accounts/login/` | Public | User authentication login |
| `/dashboard/` | Authenticated | Role-specific dashboard with overdue alerts |
| `/books/` | Authenticated | Library book catalogue & search |
| `/transactions/issued/` | Authenticated | View borrowed books & return action |
| `/transactions/requests/` | Admin / Librarian | Review and approve student borrow requests |
| `/transactions/fines/` | Student | My Fines, Pay Now button, and receipts |
| `/transactions/payments/` | Admin / Librarian | All fine records, revenue stats, and filters |
| `/transactions/receipt/<id>/` | Student (Owner) / Admin | Official printable payment receipt |

---

## 🧪 Testing the Complete Workflow

1. **Borrowing Flow**:
   - Register/login as a **Student** -> browse `/books/` -> click **Request Book**.
   - Login as a **Librarian/Admin** -> visit `/transactions/requests/` -> click **Approve**.
2. **Overdue Fine Flow**:
   - When the `due_date` passes, the student dashboard displays an **Overdue Warning Banner**.
   - Navigate to `/transactions/fines/` -> click **Pay Now** -> choose UPI / Card / NetBanking -> click **Pay & Clear Fine**.
3. **Receipt Generation**:
   - Instantly view the verified receipt and click **Print / Download Receipt**.
4. **Return Book**:
   - The Librarian navigates to `/transactions/issued/` and clicks **Return Book** to finalize the transaction and restore book stock.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
