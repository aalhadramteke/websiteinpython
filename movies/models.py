from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Customer(models.Model):
    phone = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"{self.phone} - {self.first_name} {self.last_name}"

class Movie(models.Model):
    title=models.CharField(max_length=255)
    price=models.IntegerField()
    booked_seats=models.ManyToManyField('Seat',blank=True)
    image=models.ImageField(upload_to='movie_images/', null=True, blank=True)
    created=models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} (₹{self.price})"

class Seat(models.Model):
    seat_no=models.IntegerField()
    occupant_first_name=models.CharField(max_length=255)     
    occupant_last_name=models.CharField(max_length=255)     
    occupant_email=models.EmailField(max_length=555)     
    purchase_time=models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.occupant_first_name}-{self.occupant_last_name} seat_no {self.seat_no}"

class PaymentIntent(models.Model):
    referrer=models.URLField()
    movie_title=models.CharField(max_length=255)
    seat_number=models.CharField(max_length=200)

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    first_name=models.CharField(max_length=255)
    last_name=models.CharField(max_length=255)
    email=models.EmailField(max_length=255)
    phone=models.CharField(max_length=255)
    movie=models.ForeignKey(Movie,on_delete=models.SET_NULL,null=True,blank=True)
    seat_no=models.IntegerField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    amount = models.IntegerField(default=0)  # Amount in cents or rupees
    upi_transaction_id = models.CharField(max_length=255, blank=True, null=True)  # UPI transaction reference
    booking_reference = models.CharField(max_length=100, blank=True, null=True)  # Per-payment ref, no unique
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        method_display = dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)
        return f"{self.phone} - {self.movie} - {self.status} ({method_display})"