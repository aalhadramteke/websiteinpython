from django.urls import path

from .views import index, booking, makePayement, occupiedSeats, paymentConfirm, webhook, generate_upi_qr, confirm_payment_bulk
from .auth_views import register, login_view, logout_view, get_user_info, payment_history, get_payment_history_json, debug_payment_history_json, cancel_payment, export_history, clear_all_payments

app_name='movies'

urlpatterns = [
    path('',index,name="home"),
    path('booking/', booking, name="booking"),
    path('occupied/',occupiedSeats,name="occupied_seat"),
    path('payment/',makePayement,name="payment"),
    path('confirm-payment/', confirm_payment_bulk, name='confirm-payment'),
    path("webhook/",webhook,name="webook"),
    path("payment-confirm/",paymentConfirm,name="payment-confirm"),
    path('generate-upi-qr/', generate_upi_qr, name='generate-upi-qr'),
    
    # Authentication URLs
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('user-info/', get_user_info, name='user-info'),
    path('payment-history/', payment_history, name='payment-history'),
    path('payment-history/json/', get_payment_history_json, name='payment-history-json'),
    path('cancel-payment/', cancel_payment, name='cancel-payment'),
    path('clear-all-payments/', clear_all_payments, name='clear-all-payments'),
    path('debug-history-json/', debug_payment_history_json, name='debug-history-json'),
    path('payment-history/export/', export_history, name='payment-history-export'),
]
