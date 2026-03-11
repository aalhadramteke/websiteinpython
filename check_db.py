#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movieWebsite.settings')
django.setup()

from movies.models import Movie, Payment, Customer

print("\n=== MOVIES IN DATABASE ===")
movies = Movie.objects.all()
if movies.exists():
    for m in movies:
        print(f"  {m.title}: ₹{m.price}")
    print(f"\nTotal: {movies.count()} movies")
else:
    print("  No movies found! Run: python manage.py add_movies")

print("\n=== RECENT PAYMENTS ===")
payments = Payment.objects.all().order_by('-created_at')[:10]
if payments.exists():
    for p in payments:
        amount_rupees = int(p.amount) / 100 if p.amount else 0
        print(f"  {p.phone} - {p.movie} (Seat #{p.seat_no}) - ₹{amount_rupees} - {p.status}")
else:
    print("  No payments found")

print("\n=== CUSTOMERS ===")
customers = Customer.objects.all()
print(f"Total customers: {customers.count()}")
for c in customers:
    print(f"  {c.phone} - {c.first_name} {c.last_name}")
