from django.shortcuts import render, get_object_or_404, reverse, redirect
from .models import Product, OrderDetail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import razorpay, json
from django.http import JsonResponse, HttpResponseNotFound
from .forms import ProductForm, UserRegistrationForm
from django.db.models import Sum
import datetime
from django.contrib.auth.decorators import login_required
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.contrib import messages

# required imports at top of the file
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def generate_receipt(order):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=(400, 600))

    # Header + info
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 550, "Purchase Receipt")

    p.setFont("Helvetica", 12)
    p.drawString(50, 520, f"Product: {order.product.name}")
    p.drawString(50, 500, f"Price Paid: ${order.amount}")
    p.drawString(50, 480, f"Purchased by: {order.customer_email}")
    if hasattr(order, "customer_name"):
        p.drawString(50, 460, f"Name: {order.customer_name}")
    p.drawString(50, 440, f"Date: {order.created_on.strftime('%Y-%m-%d %H:%M')}")

    # Add product image if available (download first)
    if getattr(order.product, "image", None):
        try:
            img_url = order.product.image.url
            resp = requests.get(img_url, timeout=10)
            resp.raise_for_status()
            img_io = BytesIO(resp.content)
            img = ImageReader(img_io)
            p.drawImage(img, 50, 250, width=300, height=150, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            # don't fail PDF generation if image fails; just log
            print("generate_receipt: could not add product image:", e)

    # finish PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    # Save PDF via default_storage (this works with cloudinary_storage)
    file_name = f"receipts/receipt_{order.id}.pdf"       # path/name in storage
    content = ContentFile(buffer.read())

    # If file exists, remove it first (optional)
    try:
        if default_storage.exists(file_name):
            default_storage.delete(file_name)
    except Exception:
        pass

    saved_path = default_storage.save(file_name, content)   # returns path/name in storage
    # assign to FileField properly
    order.receipt.name = saved_path
    order.save()
    buffer.close()



def index(request):
    products = Product.objects.all().order_by('-id')

    paginator = Paginator(products, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'myapp/index.html', {'products': products,'page_obj':page_obj})


def detail(request, id):
    product = get_object_or_404(Product, id=id)
    razor_publishable_key = settings.RAZOR_KEY_ID  # Test key
    return render(request, 'myapp/detail.html', {
        'product': product,
        'razor_publishable_key': razor_publishable_key
    })

@csrf_exempt
def create_checkout_session(request, id):
    if request.method == "POST":
        data = json.loads(request.body) 
        product = get_object_or_404(Product, id=id)

        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_SECRET_KEY))

        # Create Razorpay order
        order = client.order.create({
            "amount": int(product.price * 100),  # paise
            "currency": "INR",
            "payment_capture": "1"
        })

        # Save order in DB with pending status
        order_detail = OrderDetail.objects.create(
            customer_email=data.get('email'),
            product=product,
            razor_payment_id=order["id"],
            amount=product.price,
            status="PENDING"
        )

        return JsonResponse({
            "order_id": order["id"],
            "amount": order["amount"],
            "callback_url": request.build_absolute_uri(reverse("payment_handler"))
        })

    return HttpResponseNotFound()

@csrf_exempt
def verify_payment(request):
    import traceback
    try:
        data = json.loads(request.body)
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_SECRET_KEY))

        # Verify payment signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        # Mark order as PAID
        order = get_object_or_404(OrderDetail, razor_payment_id=data['razorpay_order_id'])
        order.status = "PAID"
        order.save()

        # Update product totals
        product = order.product
        product.total_sales_amount += int(order.amount)
        product.total_sales += 1
        product.save()

        # Generate receipt if not already present
        if not order.receipt:
            try:
                generate_receipt(order)
            except Exception as e:
                traceback.print_exc()
                return JsonResponse({"status": "Receipt generation failed", "error": str(e)}, status=500)


        # ✅ RETURN ORDER ID so success page knows the exact order
        return JsonResponse({
            "status": "Payment Verified",
            "order_id": order.id,
            "razorpay_order_id": order.razor_payment_id,
        })

    except razorpay.errors.SignatureVerificationError as e:

        # Mark order as FAILED
        try:
            order = OrderDetail.objects.get(razor_payment_id=data.get('razorpay_order_id'))
            order.status = "FAILED"
            order.save()
        except:
            pass

        traceback.print_exc()
        return JsonResponse({"status": "Payment Verification Failed", "error": str(e)}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "Error", "error": str(e)}, status=500)


@csrf_exempt
def payment_success_view(request):
    order = None
    # If gateway POSTs data (e.g., razorpay_order_id), prefer that to locate the order
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
        except Exception:
            data = request.POST.dict()

        order_id = data.get('razorpay_order_id') or data.get('order_id')
        if order_id:
            order = OrderDetail.objects.filter(razor_payment_id=order_id).order_by('-created_on').first()

    # If redirected via GET with order id in query params, use that to find the order
    if not order:
        get_order_id = request.GET.get('razorpay_order_id') or request.GET.get('order_id')
        if get_order_id:
            order = OrderDetail.objects.filter(razor_payment_id=get_order_id).order_by('-created_on').first()

    # Fallback: show most recent paid order for the logged-in user
    if not order:
        if request.user and request.user.is_authenticated:
            order = OrderDetail.objects.filter(customer_email=request.user.email, has_paid=True).order_by('-created_on').first()
        else:
            order = None

    return render(request, 'myapp/payment_success.html', {'order': order})


def payment_failed_view(request):
    error = request.GET.get('error', "Payment failed or cancelled.")
    return render(request, 'myapp/failed.html',{'error':error})

@login_required
def create_product(request):
    if request.method == "POST":
        product_form = ProductForm(request.POST, request.FILES)
        print("🟡 POST received:", request.POST)
        print("🟡 FILES received:", request.FILES)

        if product_form.is_valid():
            new_product = product_form.save(commit=False)
            new_product.seller = request.user
            new_product.save()
            print("✅ Product created:", new_product.id, new_product.name, new_product.seller)
            return redirect('dashboard')
        else:
            print("❌ Form errors:", product_form.errors)

    else:
        product_form = ProductForm()

    return render(request, 'myapp/create_product.html', {'product_form': product_form})



def product_edit(request,id):
    product = Product.objects.get(id=id)
    if product.seller != request.user:
        return redirect('invalid')

    product_form = ProductForm(request.POST or None,request.FILES or None,instance=product)
    if request.method == 'POST':
        if product_form.is_valid():
            product_form.save()
            return redirect('index')
    return render(request,'myapp/product_edit.html',{'product_form':product_form,'product':product})

def product_delete(request, id):
    product = get_object_or_404(Product, id=id)

    # Prevent users from deleting products they don't own
    if product.seller != request.user:
        messages.error(request, "You are not allowed to delete this product.")
        return redirect('index')

    if request.method == "POST":
        product_name = product.name  # Store name before deleting
        product.delete()
        messages.success(request, f"'{product_name}' has been successfully deleted!")
        return redirect('dashboard')  

    return render(request, 'myapp/delete.html', {'product': product})


def dashboard(request):
    products = Product.objects.filter(seller=request.user).order_by('-id')

    paginator = Paginator(products, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'myapp/dashboard.html',{'products':products,'page_obj':page_obj})

def register(request):
    if request.method == "POST":
      user_form = UserRegistrationForm(request.POST)  
      new_user = user_form.save(commit=False)
      new_user.set_password(user_form.cleaned_data['password'])
      new_user.save()
      return redirect('index')
    user_form = UserRegistrationForm()
    return render(request,'myapp/register.html',{'user_form':user_form})

def invalid(request):
    return render(request,'myapp/invalid.html')

def my_purchases(request):
    orders = OrderDetail.objects.filter(customer_email=request.user.email, status="PAID")
    return render(request,'myapp/purchases.html',{'orders':orders})

def sales(request):
    orders = OrderDetail.objects.filter(product__seller=request.user)
    total_sales = orders.aggregate(Sum('amount'))

    #365 Day Sales
    last_year = datetime.date.today() - datetime.timedelta(days=365)
    data = OrderDetail.objects.filter(product__seller=request.user,created_on__gt = last_year)
    yearly_sales = data.aggregate(Sum('amount'))
    
    #30 Day Sales
    last_month = datetime.date.today() - datetime.timedelta(days=30)
    data = OrderDetail.objects.filter(product__seller=request.user,created_on__gt = last_month)
    monthly_sales = data.aggregate(Sum('amount'))
    
    #7 Day Sales
    last_week = datetime.date.today() - datetime.timedelta(days=7)
    data = OrderDetail.objects.filter(product__seller=request.user,created_on__gt = last_week)
    weekly_sales = data.aggregate(Sum('amount'))
    
    daily_sales_sums = OrderDetail.objects.filter(product__seller=request.user).values('created_on__date').order_by('created_on__date').annotate(sum=Sum('amount'))

    product_sales_sums = OrderDetail.objects.filter(product__seller=request.user).values('product__name').order_by('product__name').annotate(sum=Sum('amount'))
    print(product_sales_sums)

    return render(request,'myapp/sales.html',{'total_sales':total_sales,'yearly_sales':yearly_sales,'monthly_sales':monthly_sales,'weekly_sales':weekly_sales,'daily_sales_sums':daily_sales_sums,'product_sales_sums':product_sales_sums})



@csrf_exempt
def payment_handler(request):
    if request.method == "POST":
        return JsonResponse({"status": "success"})
    
    return JsonResponse({"status": "Invalid Request"}, status=400)