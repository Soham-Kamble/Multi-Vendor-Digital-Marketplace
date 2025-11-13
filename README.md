# 🛒 Digital Marketplace (Django + Razorpay)

A modern **Django-based digital marketplace** where users can buy and sell digital products.  
Includes Razorpay integration, sales analytics, product management, and a fully responsive TailwindCSS UI.

---

## 🚀 Features

### 🛍️ Marketplace
- Browse all listed digital products
- Product detail pages with images & descriptions
- Pagination support

### 👤 User System
- User registration & authentication
- Role-based visibility in navigation
- Purchase history page
- Protected checkout (only logged-in users can buy)

### 💳 Payments (Razorpay)
- Secure Razorpay Checkout integration
- Payment verification webhook
- Success & failure payment pages
- Auto-generated downloadable receipts

### 📦 Seller Dashboard
- Add, edit, delete products (with image preview)
- Track total sales and revenue
- Product-wise sales analytics
- Daily / weekly / monthly sales summary

### 📊 Analytics & Charts
- Sales history table
- Revenue charts (Line + Bar using Chart.js)
- Product-wise sales performance insights

### 🎨 UI / UX
- Fully responsive with TailwindCSS
- Clean card-based layout
- Modern typography & consistent design
- Styled forms with input highlighting & previews

---

## 🧰 Tech Stack

| Layer        | Technology |
|-------------|------------|
| Backend     | Django, Python |
| Frontend    | TailwindCSS, HTML, JS |
| Charts      | Chart.js |
| Payments    | Razorpay API |
| Database    | SQLite / PostgreSQL |
| Auth        | Django Auth System |

---

## 📦 Installation Guide

### 1. Clone the repository
```bash
git clone https://github.com/your-username/digital-marketplace.git
cd digital-marketplace
```

### 2. Create Virtual Environment
```bash
python -m venv env
source env/bin/activate     # Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_SECRET_KEY=your_secret_key
```

### 5. Apply Migrations
```bash
python manage.py migrate
```

### 6. Run Server
```bash
python manage.py runserver
```

---

## 📁 Project Structure

```
myapp/
├── templates/
│   ├── index.html
│   ├── detail.html
│   ├── dashboard.html
│   ├── sales.html
│   ├── purchases.html
│   └── ...
├── models.py
├── views.py
└── urls.py
```

---

## 🧪 Future Enhancements
- Discount coupon system  
- User profile section  
- Product categories & search  
- Email notifications & invoices  
- Admin analytics dashboard  

---

⭐ **If you like this project, don't forget to star the repository!**
