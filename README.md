🎬 Movie Booking Website - Full Stack Application

A comprehensive Django-based movie ticket booking platform with user authentication, seat selection, multiple payment methods, and booking management.

📌 Project Overview

This is a **full-stack movie booking website** built with Django (Python) that allows users to:
- Browse available movies
- Select seats on an interactive seat map
- Choose from multiple payment methods (Card, UPI, Cash)
- Receive booking confirmations via email
- View and manage booking history
- Cancel bookings if needed

---

✨ Features

| 🎥 **Movie Listings** | Browse all available movies with pricing |
| 💺 **Interactive Seat Selection** | Visual seat map showing available and occupied seats |
| 👤 **User Authentication** | Registration and login with phone-based authentication |
| 💳 **Multiple Payment Methods** | Card (Paystack), UPI QR Code, Cash at counter |
| 📧 **Email Notifications** | Automatic booking confirmation emails |
| 📊 **Booking History** | View past bookings with export to Excel |
| ❌ **Booking Cancellation** | Cancel bookings and free up seats |
| 📱 **Responsive Design** | Works on desktop and mobile devices |

 Admin Features
- Movie management (add/update/delete)
- View all bookings
- Payment status tracking

 🛠 Technology Stack

 Backend

| **Django 3.x** | Web Framework |
| **Python 3.x** | Programming Language |
| **SQLite** | Default Database (easily switchable to PostgreSQL) |
| **Celery** | Asynchronous task queue for emails |
| **Django Sessions** | User session management |

Frontend

| **HTML5** | Page structure |
| **CSS3** | Styling and animations |
| **JavaScript (ES6+)** | Dynamic interactions, API calls |
| **Bootstrap** | Responsive design framework |

### Integrations

| **Paystack** | Card payment processing |
| **UPI** | Indian UPI payment gateway |
| **SMTP/Gmail** | Email notifications |

📂 Project Structure

movie-booking-website/
├── movieWebsite/              # Django project settings
│   ├── __init__.py
│   ├── asgi.py               # ASGI config
│   ├── celery.py              # Celery configuration
│   ├── settings.py            # Main settings
│   ├── urls.py                # Project URLs
│   └── wsgi.py                # WSGI config
├── movies/                    # Main application
│   ├── admin.py               # Django admin config
│   ├── apps.py                # App configuration
│   ├── auth_views.py          # Authentication views
│   ├── helpers.py             # Helper functions
│   ├── models.py              # Database models
│   ├── tests.py               # Unit tests
│   ├── urls.py                # App URLs
│   ├── views.py               # Main views
│   ├── management/
│   │   └── commands/          # Django management commands
│   │       ├── add_movies.py
│   │       └── update_movie_prices.py
│   └── migrations/            # Database migrations
├── static/                    # Static files
│   ├── backend.js             # Backend API handlers
│   ├── script.js              # Frontend JavaScript
│   └── style.css              # Styling
├── templates/                 # HTML templates
│   ├── index.html             # Home/Movie listing
│   ├── booking.html           # Seat selection
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── payment_history.html  # User bookings
│   └── email_template.html    # Email template
├── logs/                      # Application logs
├── manage.py                  # Django management script
├── check_db.py                # Database check script
└── README.md                  # This file


⚙ Key Functionalities

1. User Registration & Login
- Phone-based authentication
- Secure password hashing with Django's hasher
- Session-based login state

2. Movie Browsing
- Display all movies with images and prices
- Real-time seat availability

3. Seat Selection
- Visual seat map (grid layout)
- Real-time occupied seat tracking
- Multiple seat selection support
- Price calculation based on seat count

🚀 Installation Guide

Prerequisites
- Python 3.8 or higher
- Django 3.x
- pip package manager

Step 1: Clone Repository
bash
git clone https://github.com/aalhadramteke/movie-booking-website.git
cd movie-booking-website

Step 2: Create Virtual Environment
bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

Step 3: Install Dependencies
bash
pip install -r requirements.txt

Step 4: Environment Variables
Create a `.env` file in the project root:
env
SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
PAYSTACK_SECRET=your-paystack-secret-key
HOST_URL=http://localhost:8000


### Step 5: Run Migrations
bash
python manage.py migrate

Step 6: Create Superuser (Optional)
bash
python manage.py createsuperuser

Step 7: Add Sample Movies
bash
python manage.py add_movies

⚙ Configuration
Database
Default: SQLite (`db.sqlite3`)

For PostgreSQL, update `DATABASES` in `settings.py`:
python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'movie_booking',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


▶ How to Run

Development Server
bash
python manage.py runserver

Access at: http://localhost:8000

### Production Server
bash
Using Gunicorn
pip install gunicorn
gunicorn movieWebsite.wsgi --bind 0.0.0.0:8000


🔌 API Endpoints

| GET | `/` | Home - Movie listing |
| GET | `/booking/` | Booking page |
| POST | `/occupied/` | Get occupied seats |
| POST | `/payment/` | Initiate payment |
| GET | `/payment-confirm/` | Payment confirmation |
| POST | `/webhook/` | Paystack webhook |
| POST | `/generate-upi-qr/` | Generate UPI QR |

Authentication Endpoints

| GET/POST | `/register/` | User registration |
| GET/POST | `/login/` | User login |
| GET | `/logout/` | User logout |
| GET | `/user-info/` | Get current user |


User Endpoints

| GET | `/payment-history/` | View booking history |
| GET | `/payment-history/json/` | Get history as JSON |
| POST | `/cancel-payment/` | Cancel a booking |
| POST | `/clear-all-payments/` | Clear all bookings |
| GET | `/payment-history/export/` | Export to Excel |

🔮 Future Enhancements

- [ ] Multi-screen theater support
- [ ] Showtime management
- [ ] Food & beverage ordering
- [ ] Wallet system
- [ ] Loyalty points
- [ ] Reviews and ratings
- [ ] Movie trailers
- [ ] Social media sharing
- [ ] SMS notifications
- [ ] Dark mode

📄 License

MIT License - Feel free to use and modify this project.

👨‍💻 Author

Aalhad Ramteke
- GitHub: [@aalhadramteke](https://github.com/aalhadramteke)

🙏 Acknowledgments

- Django Documentation
- Paystack API Documentation
- Open source community

Made with ❤️ using Django
