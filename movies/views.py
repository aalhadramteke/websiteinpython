from django.http.response import HttpResponse, HttpResponseForbidden
from movies.helpers import email_customer, verify_webook
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Movie, Payment, PaymentIntent, Seat, Customer
from django.db.models import Q
import json
import requests
import base64
import uuid
from io import BytesIO
from django.contrib.auth.hashers import make_password

try:
    from ipware import get_client_ip
except ImportError:
    def get_client_ip(request):
        return None, False

try:
    import qrcode
except ImportError:
    qrcode = None

def index(request):
    movies=Movie.objects.all()
    return render(request,'index.html',{"movies":movies})

def booking(request):
    """Render the booking page with seat selection"""
    return render(request, 'booking.html')

@csrf_exempt
def occupiedSeats(request):
    data=json.loads(request.body)
    movie=Movie.objects.get(title=data["movie_title"])
    occupied=movie.booked_seats.all()
    occupied_seat=list(map(lambda seat : seat.seat_no - 1,occupied))
    return JsonResponse({"occupied_seats":occupied_seat,"movie":str(movie)})

@csrf_exempt
def makePayement(request):
    """Handle payment initiation for movie tickets"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    if not data.get("seat_list") or not isinstance(data.get("seat_list"), list):
        return JsonResponse({"error": "Seat list is required and must be a list"}, status=400)
    
    if not data.get("movie_title"):
        return JsonResponse({"error": "Movie title is required"}, status=400)
    
    seat_numbers = list(map(lambda seat: seat+1, data["seat_list"]))
    movie_title = data["movie_title"]
    payment_method = data.get("payment_method", "card").lower()
    
    if payment_method not in ["card", "upi", "cash"]:
        return JsonResponse({"error": "Invalid payment method"}, status=400)

    try:
        movie = Movie.objects.get(title=movie_title)
        cost = movie.price
    except Movie.DoesNotExist:
        return JsonResponse({"error": "Movie not found"}, status=400)

    if not seat_numbers:
        return JsonResponse({"error": "At least one seat must be selected"}, status=400)
    
    total_amount = int(cost * len(seat_numbers))
    
    customer_id = request.session.get('customer_id')
    customer = None
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            pass
    
    first_name = data.get('first_name', 'Guest')
    last_name = data.get('last_name', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    
    if email and '@' not in email:
        return JsonResponse({"error": "Invalid email format"}, status=400)

    booking_ref_base = f"{payment_method.upper()}{uuid.uuid4().hex[:10].upper()}"
    
    # Get or create customer by phone for ALL methods
    customer_obj, created = Customer.objects.get_or_create(
        phone=phone,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': make_password('temp123')
        }
    )

    # Create pending payments FOR ALL METHODS
    payments = []
    per_seat_amount = total_amount // len(seat_numbers)
    for seat_no in seat_numbers:
        booking_ref = f"{booking_ref_base}-{phone[:4] if len(phone)>=4 else 'XXXX'} -{seat_no}"
        payment = Payment.objects.create(
            customer=customer_obj,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            movie=movie,
            seat_no=seat_no,
            status='completed',
            payment_method=payment_method,
            amount=per_seat_amount * 100,  # Store as paise
            booking_reference=booking_ref
        )
        
        # Auto-book seat immediately for demo
        seat = Seat.objects.create(
            seat_no=seat_no,
            occupant_first_name=first_name,
            occupant_last_name=last_name,
            occupant_email=email
        )
        movie.booked_seats.add(seat)
        movie.save()
        
        # Send confirmation email
        try:
            email_customer(first_name, seat_no, movie.title, email)
        except:
            pass
            
        payments.append(payment)

    if payment_method == "cash":
        return JsonResponse({
            "booking_reference": booking_ref_base,
            "total_amount": total_amount,
            "message": "Please complete payment at counter",
            "confirm_url": "/confirm-payment/"
        })
    
    elif payment_method == "upi":
        return JsonResponse({
            "booking_reference": booking_ref_base,
            "total_amount": total_amount,
            "upi_string": f"upi://pay?pa=movie@upi&pn=MovieTickets&am={total_amount}&tn=Movie Booking {booking_ref_base}&tr={booking_ref_base}",
            "confirm_url": "/confirm-payment/"
        })
    
    else:  # card - test mode
        return JsonResponse({
            "success": True,
            "booking_reference": booking_ref_base,
            "test_mode": True,
            "confirm_url": "/confirm-payment/"
        })

@csrf_exempt
def confirm_payment_bulk(request):
    """Confirm pending payments by booking_reference - POST only"""
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        booking_ref_base = data.get('booking_reference')
        if not booking_ref_base:
            return JsonResponse({"error": "booking_reference required"}, status=400)
        
        # Find pending payments by base ref pattern
        payments = Payment.objects.filter(
            booking_reference__startswith=booking_ref_base,
            status='completed'
        )
        
        if not payments.exists():
            return JsonResponse({"error": f"No pending payments found for ref {booking_ref_base}"}, status=404)
        
        confirmed = 0
        for payment in payments:
            movie = payment.movie
            if movie:
                # Book seat
                seat = Seat.objects.create(
                    seat_no=payment.seat_no,
                    occupant_first_name=payment.first_name,
                    occupant_last_name=payment.last_name,
                    occupant_email=payment.email
                )
                movie.booked_seats.add(seat)
                movie.save()
                
                payment.status = 'completed'
                payment.save()
                confirmed += 1
                
                # Email
                try:
                    email_customer(payment.first_name, payment.seat_no, movie.title, payment.email)
                except:
                    pass
        
        return JsonResponse({
            "success": True,
            "confirmed": confirmed,
            "message": f"Confirmed {confirmed} payments for ref {booking_ref_base}"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def webhook(request):
    """Handle Paystack webhook for payment confirmation"""
    # ... (existing webhook code unchanged)

@csrf_exempt
def generate_upi_qr(request):
    """Generate UPI QR code for payment"""
    # ... (existing code unchanged)

def paymentConfirm(request):
    """Display payment confirmation page showing recent bookings"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        from django.shortcuts import redirect
        return redirect('movies:login')
    
    try:
        customer = Customer.objects.get(id=customer_id)
        payments_count = customer.payments.count()
    except Customer.DoesNotExist:
        from django.shortcuts import redirect
        return redirect('movies:login')
    
    return render(request, 'payment_history.html', {
        'customer': customer,
        'payments_count': payments_count
    })

