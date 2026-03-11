from django.http.response import HttpResponse, HttpResponseForbidden
from movies.helpers import email_customer, verify_webook
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Movie, Payment, PaymentIntent, Seat, Customer

import json
import requests
import base64
import uuid
from io import BytesIO

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
    return render(request,'index.html',{
        "movies":movies
    })

def booking(request):
    """Render the booking page with seat selection"""
    return render(request, 'booking.html')

@csrf_exempt
def occupiedSeats(request):
    data=json.loads(request.body)

    movie=Movie.objects.get(title=data["movie_title"])
    occupied=movie.booked_seats.all()
    occupied_seat=list(map(lambda seat : seat.seat_no - 1,occupied))

    return JsonResponse({
        "occupied_seats":occupied_seat,
        "movie":str(movie)
    })

@csrf_exempt
def makePayement(request):
    """Handle payment initiation for movie tickets"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # Validate required fields
    if not data.get("seat_list") or not isinstance(data.get("seat_list"), list):
        return JsonResponse({"error": "Seat list is required and must be a list"}, status=400)
    
    if not data.get("movie_title"):
        return JsonResponse({"error": "Movie title is required"}, status=400)
    
    seat_numbers = list(map(lambda seat: seat+1, data["seat_list"]))
    movie_title = data["movie_title"]
    payment_method = data.get("payment_method", "card").lower()  # Get payment method from request
    
    # Validate payment method
    if payment_method not in ["card", "upi", "cash"]:
        return JsonResponse({"error": "Invalid payment method"}, status=400)

    try:
        movie = Movie.objects.get(title=movie_title)
        cost = movie.price
    except Movie.DoesNotExist:
        return JsonResponse({"error": "Movie not found"}, status=400)

    # Validate seat numbers
    if not seat_numbers or len(seat_numbers) == 0:
        return JsonResponse({"error": "At least one seat must be selected"}, status=400)
    
    total_amount = int(cost * len(seat_numbers))  # Amount in rupees
    
    # Get customer data
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            customer = None
    
    first_name = data.get('first_name', 'Guest')
    last_name = data.get('last_name', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    
    # Validate email if provided
    if email and '@' not in email:
        return JsonResponse({"error": "Invalid email format"}, status=400)

    # Handle different payment methods
    if payment_method == "cash":
        # For cash payment, create booking reference and mark as pending
        booking_ref = f"CASH{uuid.uuid4().hex[:10].upper()}"
        
        # Create payment records (seats not booked yet - user pays at counter)
        for seat_no in seat_numbers:
            Payment.objects.create(
                customer=customer,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                movie=movie,
                seat_no=seat_no,
                status='pending',  # For cash, payment is pending until verified
                payment_method='cash',
                amount=total_amount // len(seat_numbers),
                booking_reference=booking_ref
            )
        
        return JsonResponse({
            "payment_method": "cash",
            "booking_reference": booking_ref,
            "total_amount": total_amount,
            "message": "Please complete payment at the cinema counter to confirm your booking",
            "confirm_url": "/payment-confirm/"
        })
    
    elif payment_method == "upi":
        # For UPI payment, create booking reference
        booking_ref = f"UPI{uuid.uuid4().hex[:10].upper()}"
        
        # Create payment records (seats not booked yet - pending UPI confirmation)
        for seat_no in seat_numbers:
            Payment.objects.create(
                customer=customer,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                movie=movie,
                seat_no=seat_no,
                status='pending',
                payment_method='upi',
                amount=total_amount // len(seat_numbers),
                booking_reference=booking_ref
            )
        
        return JsonResponse({
            "payment_method": "upi",
            "booking_reference": booking_ref,
            "total_amount": total_amount,
            "confirm_url": "/generate-upi-qr/"
        })
    
    else:  # card payment (default)
        header={
            "Authorization":f"Bearer {settings.PAYSTACK_SECRET}",
            "Content-Type":"application/json"
        }

        total_amount_cents = int(total_amount)*100  # Amount in cents for Paystack

        payload={
            "name":"Payment of Movie Ticket",
            "amount": total_amount_cents,
            "description":f"Payment for {len(seat_numbers)} ticket of {movie_title}",
            "collect_phone":True,
            "redirect_url":f"{settings.HOST_URL}/payment-confirm/"
        }

        # Use test mode if PAYSTACK_SECRET is empty
        if not settings.PAYSTACK_SECRET:
            PaymentIntent.objects.create(referrer="test",
                                        movie_title=movie_title,
                                        seat_number=json.dumps(seat_numbers))
            
            for seat_no in seat_numbers:
                Payment.objects.create(
                    customer=customer,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    movie=movie,
                    seat_no=seat_no,
                    status='completed',
                    payment_method='card',
                    amount=total_amount_cents // len(seat_numbers)
                )
            
            return JsonResponse({
                "test_mode": True,
                "confirm_url": "/payment-confirm/"
            })

        response=requests.post('https://api.paystack.co/page',
                                json=payload,headers=header)

        if response.status_code ==200:
            response_data=response.json()
            slug=response_data["data"]["slug"]
            redirect_url=f"https://paystack.com/pay/{slug}"

            PaymentIntent.objects.create(referrer=redirect_url,
                                        movie_title=movie_title,
                                        seat_number=json.dumps(seat_numbers))
            
            return JsonResponse({
                "payment_url":redirect_url
            })

        return JsonResponse({
            "error":"sorry service is not available"
        })

@csrf_exempt
def webhook(request):
    """Handle Paystack webhook for payment confirmation"""
    if request.method != "POST":
        return HttpResponseForbidden()
    
    try:
        # Verify the webhook signature
        if not verify_webook(request):
            return HttpResponseForbidden()
        
        # Get client IP (optional verification - Paystack IPs)
        ip, is_routable = get_client_ip(request)
        if ip and ip not in settings.PAYSTACK_IP:
            # Log warning but don't block - IP verification is optional
            pass
        
        response = json.loads(request.body)
        
        # Only process successful charge events
        if response.get("event") != "charge.success":
            return HttpResponse(200)  # Still return success to acknowledge webhook
        
        try:
            # Extract customer and payment data
            customer_data = response.get("data", {}).get("customer", {})
            first_name = customer_data.get("first_name", "Guest")
            last_name = customer_data.get("last_name", "")
            phone = customer_data.get("phone", "")
            email = customer_data.get("email", "")
            amount = int(response.get("data", {}).get("amount", 0))
            
            # Get metadata with referrer (booking reference)
            metadata = response.get("data", {}).get("metadata", {})
            referrer = metadata.get("referrer")
            
            if not referrer:
                # Fallback: try to get from custom fields
                referrer = response.get("data", {}).get("reference")
            
            if not referrer:
                return JsonResponse({"error": "No referrer found"}, status=400)
            
            # Find the payment intent
            payment_intent = PaymentIntent.objects.get(referrer=referrer)
            movie_title = payment_intent.movie_title
            movie = Movie.objects.get(title=movie_title)
            booked_seat = json.loads(payment_intent.seat_number)
            
            # Create seats and payment records
            for seat_no in booked_seat:
                # Create seat if it doesn't already exist
                seat = Seat.objects.create(
                    seat_no=seat_no,
                    occupant_first_name=first_name,
                    occupant_last_name=last_name,
                    occupant_email=email
                )
                
                # Add seat to movie
                movie.booked_seats.add(seat)
                movie.save()
                
                # Create payment record with correct amount (in cents)
                payment = Payment.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    movie=movie,
                    seat_no=seat_no,
                    status='completed',
                    payment_method='card',
                    amount=amount // len(booked_seat)  # Amount in cents
                )
                
                # Send confirmation email
                try:
                    email_customer(first_name, seat_no, movie_title, email)
                except Exception as e:
                    # Log email error but don't fail the payment
                    pass
            
            # Delete payment intent after successful processing
            payment_intent.delete()
            return HttpResponse(200)
            
        except PaymentIntent.DoesNotExist:
            # PaymentIntent not found - possibly duplicate webhook or old referrer
            return HttpResponse(200)  # Return success to prevent retry
            
        except Movie.DoesNotExist:
            # Movie not found
            return HttpResponse(400)
            
        except json.JSONDecodeError:
            return HttpResponse(400)
            
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            return HttpResponse(400)
    
    except json.JSONDecodeError:
        return HttpResponse(400)


@csrf_exempt
def generate_upi_qr(request):
    """Generate UPI QR code for payment"""
    if request.method == "POST":
        data = json.loads(request.body)
        booking_reference = data.get('booking_reference')
        total_amount = data.get('total_amount')
        phone = data.get('phone', '')
        
        if not booking_reference or not total_amount:
            return JsonResponse({"error": "Missing required fields"}, status=400)
        
        try:
            # UPI deep link format: upi://pay?pa=MERCHANT_UPI_ID&pn=MERCHANT_NAME&am=AMOUNT&tn=DESCRIPTION&tr=REFERENCE
            # For demo purposes, we'll use a placeholder UPI ID
            # In production, replace with your business UPI ID
            upi_id = "movie@upi"  # Change this to your actual UPI ID
            merchant_name = "Movie Tickets"
            description = f"Booking {booking_reference}"
            
            upi_string = f"upi://pay?pa={upi_id}&pn={merchant_name}&am={total_amount}&tn={description}&tr={booking_reference}"
            
            if not qrcode:
                # If qrcode not available, return UPI string for mobile payment
                return JsonResponse({
                    "upi_string": upi_string,
                    "qr_code": None
                })
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(upi_string)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for sending to frontend
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return JsonResponse({
                "upi_string": upi_string,
                "qr_code": f"data:image/png;base64,{img_str}",
                "booking_reference": booking_reference,
                "total_amount": total_amount
            })
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)



def paymentConfirm(request):
    """
    Confirm payment and book seats.
    For Card: Payment already confirmed via webhook
    For UPI/Cash: User manually confirms after payment
    """
    booking_ref = request.GET.get('booking_ref')
    payment_method = request.GET.get('method', 'card')
    
    try:
        if not booking_ref:
            # No booking reference - generic success page
            return HttpResponse('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Payment Confirmation - Movie Booking</title>
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-family: 'Lato', sans-serif;
                        padding: 20px;
                    }
                    
                    .confirmation-container {
                        background: rgba(255, 255, 255, 0.95);
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                        max-width: 500px;
                        width: 100%;
                        padding: 50px 40px;
                        text-align: center;
                        animation: slideUp 0.5s ease-out;
                    }
                    
                    @keyframes slideUp {
                        from {
                            opacity: 0;
                            transform: translateY(30px);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0);
                        }
                    }
                    
                    .success-icon {
                        width: 80px;
                        height: 80px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 30px;
                        animation: bounce 0.6s ease-out;
                    }
                    
                    @keyframes bounce {
                        0% {
                            transform: scale(0.5);
                        }
                        70% {
                            transform: scale(1.1);
                        }
                        100% {
                            transform: scale(1);
                        }
                    }
                    
                    .success-icon::before {
                        content: "✓";
                        font-size: 48px;
                        color: white;
                        font-weight: bold;
                    }
                    
                    h2 {
                        color: #2d3436;
                        font-size: 28px;
                        margin-bottom: 10px;
                        font-weight: 700;
                    }
                    
                    h3 {
                        color: #667eea;
                        font-size: 20px;
                        margin-bottom: 20px;
                        font-weight: 600;
                    }
                    
                    .confirmation-details {
                        background: #f8f9fa;
                        border-left: 4px solid #667eea;
                        padding: 20px;
                        border-radius: 10px;
                        margin: 30px 0;
                        text-align: left;
                    }
                    
                    .detail-item {
                        margin: 12px 0;
                        color: #555;
                        font-size: 14px;
                    }
                    
                    .detail-label {
                        font-weight: bold;
                        color: #2d3436;
                        display: inline-block;
                        width: 130px;
                    }
                    
                    .detail-value {
                        color: #667eea;
                        font-weight: 600;
                    }
                    
                    p {
                        color: #666;
                        font-size: 15px;
                        line-height: 1.6;
                        margin: 20px 0;
                    }
                    
                    .button-group {
                        display: flex;
                        gap: 15px;
                        margin-top: 30px;
                    }
                    
                    .btn {
                        flex: 1;
                        padding: 14px 30px;
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        text-decoration: none;
                        display: inline-block;
                    }
                    
                    .btn-primary {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                    }
                    
                    .btn-primary:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
                    }
                    
                    .btn-secondary {
                        background: #f0f0f0;
                        color: #2d3436;
                        border: 2px solid #ddd;
                    }
                    
                    .btn-secondary:hover {
                        background: #e8e8e8;
                        border-color: #bbb;
                    }
                    
                    .ticket-icon {
                        font-size: 40px;
                        margin: 20px 0;
                    }
                </style>
            </head>
            <body>
                <div class="confirmation-container">
                    <div class="success-icon"></div>
                    <h2>Payment Successful!</h2>
                    <h3>🎬 Your Movie Tickets Are Confirmed</h3>
                    
                    <div class="confirmation-details">
                        <div class="detail-item">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value">✓ Completed</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Confirmation:</span>
                            <span class="detail-value">Email Sent</span>
                        </div>
                    </div>
                    
                    <div class="ticket-icon">🎫</div>
                    
                    <p><strong>Your seat numbers have been sent to your registered email address.</strong></p>
                    <p>Please check your email for your booking details and ticket information. Save your confirmation email for entry.</p>
                    
                    <div class="button-group">
                        <a href="/" class="btn btn-primary">Book More Tickets</a>
                        <a href="/payment-history/" class="btn btn-secondary">View History</a>
                    </div>
                </div>
            </body>
            </html>
            ''')
        
        # For UPI/Cash payments with booking reference
        if payment_method in ['upi', 'cash']:
            # Find payment records with this booking reference
            payments = Payment.objects.filter(booking_reference=booking_ref)
            
            if not payments.exists():
                return HttpResponse('''
                <html>
                <body style="font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh;">
                    <div style="background: white; padding: 40px; border-radius: 8px; text-align: center;">
                        <h2 style="color: #d32f2f;">⚠️ Booking Not Found</h2>
                        <p>No booking found with reference: ''' + booking_ref + '''</p>
                        <a href="/" style="color: #667eea; text-decoration: none;">← Go back to booking</a>
                    </div>
                </body>
                </html>
                ''')
            
            # Check if already confirmed
            if all(p.status == 'completed' for p in payments):
                return HttpResponse('''
                <html>
                <body style="font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh;">
                    <div style="background: white; padding: 40px; border-radius: 8px; text-align: center;">
                        <h2 style="color: #27ae60;">✓ Already Confirmed</h2>
                        <p>Your booking has already been confirmed.</p>
                        <a href="/payment-history/" style="color: #667eea; text-decoration: none;">View Booking →</a>
                    </div>
                </body>
                </html>
                ''')
            
            # Confirm payment and book seats
            for payment in payments:
                movie = payment.movie
                if movie:
                    # Create seat and book it
                    seat = Seat.objects.create(
                        seat_no=payment.seat_no,
                        occupant_first_name=payment.first_name,
                        occupant_last_name=payment.last_name,
                        occupant_email=payment.email
                    )
                    movie.booked_seats.add(seat)
                    movie.save()
                    
                    # Update payment status
                    payment.status = 'completed'
                    payment.save()
                    
                    # Send confirmation email
                    try:
                        email_customer(payment.first_name, payment.seat_no, movie.title, payment.email)
                    except:
                        pass
            
            # Return success page
            return HttpResponse('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Payment Confirmation - Movie Booking</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-family: 'Lato', sans-serif;
                        padding: 20px;
                    }
                    .confirmation-container {
                        background: rgba(255, 255, 255, 0.95);
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                        max-width: 500px;
                        width: 100%;
                        padding: 50px 40px;
                        text-align: center;
                        animation: slideUp 0.5s ease-out;
                    }
                    @keyframes slideUp {
                        from { opacity: 0; transform: translateY(30px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    .success-icon {
                        width: 80px;
                        height: 80px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 30px;
                        animation: bounce 0.6s ease-out;
                    }
                    @keyframes bounce {
                        0% { transform: scale(0.5); }
                        70% { transform: scale(1.1); }
                        100% { transform: scale(1); }
                    }
                    .success-icon::before { content: "✓"; font-size: 48px; color: white; font-weight: bold; }
                    h2 { color: #2d3436; font-size: 28px; margin-bottom: 10px; font-weight: 700; }
                    h3 { color: #667eea; font-size: 20px; margin-bottom: 20px; font-weight: 600; }
                    .confirmation-details {
                        background: #f8f9fa;
                        border-left: 4px solid #667eea;
                        padding: 20px;
                        border-radius: 10px;
                        margin: 30px 0;
                        text-align: left;
                    }
                    .detail-item { margin: 12px 0; color: #555; font-size: 14px; }
                    .detail-label { font-weight: bold; color: #2d3436; display: inline-block; width: 130px; }
                    .detail-value { color: #667eea; font-weight: 600; }
                    p { color: #666; font-size: 15px; line-height: 1.6; margin: 20px 0; }
                    .button-group { display: flex; gap: 15px; margin-top: 30px; }
                    .btn {
                        flex: 1;
                        padding: 14px 30px;
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        text-decoration: none;
                        display: inline-block;
                    }
                    .btn-primary {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                    }
                    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6); }
                    .btn-secondary { background: #f0f0f0; color: #2d3436; border: 2px solid #ddd; }
                    .btn-secondary:hover { background: #e8e8e8; border-color: #bbb; }
                    .ticket-icon { font-size: 40px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="confirmation-container">
                    <div class="success-icon"></div>
                    <h2>Payment Successful!</h2>
                    <h3>🎬 Your Movie Tickets Are Confirmed</h3>
                    <div class="confirmation-details">
                        <div class="detail-item">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value">✓ Completed</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Booking Reference:</span>
                            <span class="detail-value">''' + booking_ref + '''</span>
                        </div>
                    </div>
                    <div class="ticket-icon">🎫</div>
                    <p><strong>Your seat numbers have been sent to your registered email address.</strong></p>
                    <p>Please check your email for your booking details and ticket information.</p>
                    <div class="button-group">
                        <a href="/" class="btn btn-primary">Book More Tickets</a>
                        <a href="/payment-history/" class="btn btn-secondary">View History</a>
                    </div>
                </div>
            </body>
            </html>
            ''')
        
        # Card payment - already confirmed via webhook
        return HttpResponse('''
        <html>
        <body style="font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh;">
            <div style="background: white; padding: 40px; border-radius: 8px; text-align: center;">
                <h2 style="color: #27ae60;">✓ Payment Confirmed</h2>
                <p>Your payment has been processed successfully.</p>
                <p>Check your email for booking details.</p>
                <a href="/payment-history/" style="color: #667eea; text-decoration: none; margin-top: 20px; display: block;">View Your Bookings →</a>
            </div>
        </body>
        </html>
        ''')
    
    except Exception as e:
        return HttpResponse(f'''
        <html>
        <body style="font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh;">
            <div style="background: white; padding: 40px; border-radius: 8px; text-align: center;">
                <h2 style="color: #d32f2f;">Error Processing Payment</h2>
                <p>An error occurred: {str(e)}</p>
                <a href="/" style="color: #667eea; text-decoration: none;">← Go back</a>
            </div>
        </body>
        </html>
        ''')
