from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Customer
import json

@csrf_exempt
def register(request):
    """Handle customer registration"""
    if request.method == 'POST':
        data = json.loads(request.body)
        phone = data.get('phone')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        email = data.get('email', '')
        password = data.get('password', '')
        
        if not phone:
            return JsonResponse({'error': 'Phone number is required'}, status=400)
        
        if Customer.objects.filter(phone=phone).exists():
            return JsonResponse({'error': 'Phone number already registered'}, status=400)
        
        try:
            customer = Customer(
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            customer.set_password(password)
            customer.save()
            
            # Store in session
            request.session['customer_id'] = customer.id
            request.session['customer_phone'] = customer.phone
            
            return JsonResponse({
                'success': True,
                'message': 'Registration successful',
                'customer_id': customer.id,
                'phone': customer.phone,
                'name': f"{customer.first_name} {customer.last_name}".strip()
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    # Render register template for GET requests
    return render(request, 'register.html')

@csrf_exempt
def login_view(request):
    """Handle customer login"""
    if request.method == 'POST':
        data = json.loads(request.body)
        phone = data.get('phone')
        password = data.get('password')
        
        if not phone or not password:
            return JsonResponse({'error': 'Phone and password required'}, status=400)
        
        try:
            customer = Customer.objects.get(phone=phone)
            if customer.check_password(password):
                # Store in session
                request.session['customer_id'] = customer.id
                request.session['customer_phone'] = customer.phone
                
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'customer_id': customer.id,
                    'phone': customer.phone,
                    'name': f"{customer.first_name} {customer.last_name}".strip()
                })
            else:
                return JsonResponse({'error': 'Invalid password'}, status=400)
        except Customer.DoesNotExist:
            return JsonResponse({'error': 'Phone number not registered'}, status=400)
    
    # Render login template for GET requests
    return render(request, 'login.html')

@csrf_exempt
def logout_view(request):
    """Handle customer logout"""
    if 'customer_id' in request.session:
        del request.session['customer_id']
    if 'customer_phone' in request.session:
        del request.session['customer_phone']
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})

def get_user_info(request):
    """Get current logged-in user info"""
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
            return JsonResponse({
                'authenticated': True,
                'customer_id': customer.id,
                'phone': customer.phone,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'email': customer.email,
                'name': f"{customer.first_name} {customer.last_name}".strip()
            })
        except Customer.DoesNotExist:
            del request.session['customer_id']
    
    return JsonResponse({'authenticated': False})

def payment_history(request):
    """Display payment history page for logged-in user"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('movies:login')
    # Render the payment history template
    return render(request, 'payment_history.html')

@csrf_exempt
def get_payment_history_json(request):
    """Get payment history as JSON for logged-in user"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        customer = Customer.objects.get(id=customer_id)
        payments = customer.payments.all()
        payment_list = []
        
        for payment in payments:
            payment_list.append({
                'id': payment.id,
                'movie': payment.movie.title if payment.movie else 'N/A',
                'seats': payment.seat_no,
                'first_name': payment.first_name,
                'last_name': payment.last_name,
                'email': payment.email,
                'phone': payment.phone,
                'status': payment.status,
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else 'N/A',
                'updated_at': payment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'payments': payment_list,
            'total': len(payment_list)
        })
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=400)

@csrf_exempt
# cancel a single payment/seat

def cancel_payment(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    try:
        data = json.loads(request.body)
        pid = data.get('payment_id')
        from .models import Payment, Seat
        payment = Payment.objects.get(id=pid, customer_id=customer_id)
        if payment.status == 'cancelled':
            return JsonResponse({'error': 'Already cancelled'})
        # remove associated seat(s) from movie
        movie = payment.movie
        if movie:
            seats = movie.booked_seats.filter(seat_no=payment.seat_no)
            for seat in seats:
                movie.booked_seats.remove(seat)
                seat.delete()
        payment.status = 'cancelled'
        payment.save()
        return JsonResponse({'success': True})
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def clear_all_payments(request):
    """Clear all payment entries for the current customer"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        from .models import Payment, Seat
        customer = Customer.objects.get(id=customer_id)
        
        # Get all payments for this customer
        payments = Payment.objects.filter(customer_id=customer_id)
        
        # For each payment, remove associated seats from movies
        for payment in payments:
            movie = payment.movie
            if movie:
                # Find and remove booked seats by seat number
                try:
                    # Seat number is stored as integer in Payment model
                    seats = movie.booked_seats.filter(seat_no=payment.seat_no)
                    for seat in seats:
                        movie.booked_seats.remove(seat)
                        seat.delete()
                except Exception as e:
                    # Log the error but continue
                    pass
        
        # Delete all payments
        payment_count = payments.count()
        payments.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Cleared {payment_count} payment entries',
            'cleared_count': payment_count
        })
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def export_history(request):
    """Export payment history as Excel file"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('movies:login')
    
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return redirect('movies:login')
    
    try:
        from openpyxl import Workbook
        
        payments = customer.payments.all()
        wb = Workbook()
        ws = wb.active
        ws.title = 'Payment History'
        
        # Add headers
        headers = ['ID', 'Movie', 'Seat', 'Amount (₹)', 'First Name', 'Last Name', 'Email', 'Phone', 'Status', 'Booked On', 'Updated On']
        ws.append(headers)
        
        # Add payment data
        for p in payments:
            ws.append([
                p.id,
                p.movie.title if p.movie else '',
                p.seat_no,
                p.amount / 100 if p.amount else 0,  # Convert cents to rupees
                p.first_name,
                p.last_name,
                p.email,
                p.phone,
                p.status,
                p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else '',
                p.updated_at.strftime('%Y-%m-%d %H:%M:%S') if p.updated_at else ''
            ])
        
        # Create HTTP response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=payment_history.xlsx'
        wb.save(response)
        return response
        
    except ImportError:
        return JsonResponse({'error': 'openpyxl package not installed. Please run: pip install openpyxl'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Error generating Excel file: {str(e)}'}, status=500)
