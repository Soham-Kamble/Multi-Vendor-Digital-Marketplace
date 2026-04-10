# 🛒 Digital Marketplace — Django REST API

A production-deployed **multi-vendor digital marketplace** built with Django REST Framework and JWT authentication.  
Sellers can list and manage digital products. Buyers can browse, purchase, and track orders.  
Includes Razorpay payment integration, seller analytics, and a fully responsive TailwindCSS UI.

🔗 **Live Demo:** https://multi-vendor-digital-marketplace.onrender.com  
📂 **GitHub:** [github.com/Soham-Kamble/Multi-Vendor-Digital-Marketplace](https://github.com/Soham-Kamble/Multi-Vendor-Digital-Marketplace)

---

## 🧰 Tech Stack

| Layer       | Technology                              |
|-------------|------------------------------------------|
| Backend     | Django, Django REST Framework, Python    |
| Auth        | JWT Authentication (SimpleJWT)           |
| Payments    | Razorpay API                             |
| Database    | PostgreSQL                               |
| Frontend    | TailwindCSS, HTML, JavaScript            |
| Charts      | Chart.js                                 |
| Storage     | Cloudinary                               |
| Deployment  | Render                                   |

---

## 🚀 Features

### 🔐 Authentication (JWT)
- Register, login, logout via REST API
- Access tokens (15 min) + Refresh tokens (7 days)
- Refresh token blacklisting on logout
- All protected endpoints require `Authorization: Bearer <token>`

### 🛍️ Marketplace
- Browse all listed digital products (public)
- Product detail pages with images and descriptions
- Pagination support

### 👤 Seller
- Create, edit, delete own products (JWT protected)
- Seller dashboard — view only your own listings
- Sales analytics — total, yearly, monthly, weekly breakdowns
- Revenue charts using Chart.js

### 💳 Payments (Razorpay)
- Secure Razorpay Checkout integration
- Server-side payment signature verification
- Order confirmation and failure handling
- Auto-generated downloadable receipts

### 🧾 Buyer
- Purchase history — all paid orders
- Receipt download per order

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Register new user |
| POST | `/api/auth/login/` | No | Get access + refresh tokens |
| POST | `/api/auth/refresh/` | No | Refresh access token |
| POST | `/api/auth/logout/` | Yes | Blacklist refresh token |

### Products
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/products/` | No | List all products |
| GET | `/api/products/<id>/` | No | Product detail |
| POST | `/api/products/create/` | Yes | Create product (seller only) |
| PUT | `/api/products/<id>/edit/` | Yes | Edit own product |
| DELETE | `/api/products/<id>/delete/` | Yes | Delete own product |

### Dashboard & Analytics
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/dashboard/` | Yes | Seller's own product listings |
| GET | `/api/sales/` | Yes | Seller's sales analytics |
| GET | `/api/purchases/` | Yes | Buyer's paid orders |

---

## 🧪 Testing the API

You can test all endpoints using Postman or a `.http` file.

**1. Register**
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "soham",
  "email": "soham@test.com",
  "password": "test1234"
}
```

**2. Login — copy the access + refresh tokens from response**
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "soham",
  "password": "test1234"
}
```

**3. Access protected endpoint**
```http
GET /api/dashboard/
Authorization: Bearer <access_token>
```

**4. Logout**
```http
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/Soham-Kamble/Multi-Vendor-Digital-Marketplace
cd Multi-Vendor-Digital-Marketplace
```

### 2. Create virtual environment
```bash
python -m venv env
source env/bin/activate     # Windows: env\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:

```
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_SECRET_KEY=your_secret_key
SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=your_postgresql_url
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
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
├── templates/         # Django HTML templates
├── models.py          # Product, OrderDetail models
├── serializers.py     # DRF serializers
├── views.py           # Template views + DRF API views
├── urls.py            # URL routing
└── forms.py           # Django forms
```
---

## 🔮 Upcoming
- Redis caching on product listings
- Docker + docker-compose setup
- Celery for async receipt generation

---

⭐ If you find this project useful, consider starring the repository!
