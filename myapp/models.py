from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    name  = models.CharField(max_length=100)
    description  = models.CharField(max_length=100)
    price = models.FloatField()
    
    total_sales_amount = models.IntegerField(default=0)
    total_sales = models.IntegerField(default=0)

    # Product images stored in Cloudinary
    image = CloudinaryField('image', blank=True, null=True, folder='products')
    
    def __str__(self):
        return self.name


class OrderDetail(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    )

    customer_email = models.EmailField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.IntegerField()
    razor_payment_id = models.CharField(max_length=200)
    has_paid = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    receipt = CloudinaryField(
        resource_type='raw',      # raw for PDF
        folder='receipts',
        null=True,
        blank=True,
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")  
    razor_order_id = models.CharField(max_length=200, null=True, blank=True)
