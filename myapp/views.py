from django.shortcuts import render, get_object_or_404, reverse, redirect
from .models import Product, OrderDetail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import razorpay, json
from django.http import JsonResponse, HttpResponseNotFound, FileResponse
from .forms import ProductForm, UserRegistrationForm
from django.db.models import Sum
import datetime
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from django.core.paginator import Paginator
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, ProductSerializer, ProductWriteSerializer, OrderDetailSerializer

from django.core.cache import cache
from django.views.decorators.cache import cache_page
import redis

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
            "payment_capture": 1
        })

        # Save order in DB with pending status
        order_detail = OrderDetail.objects.create(
            customer_email=data.get('email'),
            product=product,
            razor_order_id = order["id"],
            amount=product.price,
            status="PENDING"
        )

        return JsonResponse({
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "callback_url": request.build_absolute_uri(reverse("payment_handler"))
        })

    return HttpResponseNotFound()

@csrf_exempt
def verify_payment(request):
    import traceback
    try:
        data = json.loads(request.body)
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_SECRET_KEY))

        # 1) verify signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        # 2) find order (search by razor_order_id)
        order = get_object_or_404(OrderDetail, razor_order_id=data['razorpay_order_id'])

        # 3) save payment id and mark PAID
        order.razor_payment_id = data['razorpay_payment_id']
        order.status = "PAID"
        order.has_paid = True
        order.save()

        # 4) update product totals
        product = order.product
        product.total_sales_amount += int(order.amount)
        product.total_sales += 1
        product.save()

        # 5) generate receipt (if not present)

        return JsonResponse({
            "status": "Payment Verified",
            "order_id": order.id,
            "razorpay_order_id": order.razor_order_id,
        })

    except razorpay.errors.SignatureVerificationError as e:
        # mark failed
        try:
            o = OrderDetail.objects.filter(razor_order_id=data.get('razorpay_order_id')).first()
            if o:
                o.status = "FAILED"
                o.save()
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
        # Try both order_id (DB primary key) and razorpay_order_id
        get_order_id = request.GET.get('order_id')
        if get_order_id:
            try:
                order = OrderDetail.objects.get(id=int(get_order_id))
            except (OrderDetail.DoesNotExist, ValueError):
                pass
        
        # Fallback: try razorpay_order_id
        if not order:
            razorpay_id = request.GET.get('razorpay_order_id')
            if razorpay_id:
                order = OrderDetail.objects.filter(razor_payment_id=razorpay_id).order_by('-created_on').first()

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
      messages.success(request, "Account created successfully! Please login.")
      return redirect('login')
    user_form = UserRegistrationForm()
    return render(request,'myapp/register.html',{'user_form':user_form})

def invalid(request):
    return render(request,'myapp/invalid.html')

def my_purchases(request):
    orders = OrderDetail.objects.filter(
        customer_email=request.user.email,
        status="PAID"
    ).order_by('-created_on')  # newest first

    return render(request,'myapp/purchases.html',{'orders':orders})


def sales(request):

    # ONLY include paid orders
    orders = OrderDetail.objects.filter(
        product__seller=request.user,
        status="PAID"
    )

    total_sales = orders.aggregate(Sum('amount'))

    last_year = datetime.date.today() - datetime.timedelta(days=365)
    yearly_sales = orders.filter(created_on__gt=last_year).aggregate(Sum('amount'))

    last_month = datetime.date.today() - datetime.timedelta(days=30)
    monthly_sales = orders.filter(created_on__gt=last_month).aggregate(Sum('amount'))

    last_week = datetime.date.today() - datetime.timedelta(days=7)
    weekly_sales = orders.filter(created_on__gt=last_week).aggregate(Sum('amount'))

    daily_sales_sums = orders.values('created_on__date') \
                             .order_by('created_on__date') \
                             .annotate(sum=Sum('amount'))

    product_sales_sums = orders.values('product__name') \
                               .order_by('product__name') \
                               .annotate(sum=Sum('amount'))

    return render(request, 'myapp/sales.html', {
        'total_sales': total_sales,
        'yearly_sales': yearly_sales,
        'monthly_sales': monthly_sales,
        'weekly_sales': weekly_sales,
        'daily_sales_sums': daily_sales_sums,
        'product_sales_sums': product_sales_sums
    })



@login_required
def download_receipt(request, order_id):
    """Download receipt PDF for a specific order"""
    try:
        order = OrderDetail.objects.get(id=order_id)
        # Verify user owns this order (via email or user account)
        if order.customer_email != request.user.email:
            return HttpResponseNotFound("Order not found or access denied")
        
        if not order.receipt:
            return HttpResponseNotFound("Receipt not generated yet")
        
        # Open the receipt file and return it
        receipt_file = order.receipt.open('rb')
        response = FileResponse(receipt_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{order.id}.pdf"'
        return response
    except OrderDetail.DoesNotExist:
        return HttpResponseNotFound("Order not found")
    except Exception as e:
        print(f"Receipt download error: {e}")
        return HttpResponseNotFound("Could not download receipt")


# Alternative: Direct URL redirect to Cloudinary
@login_required
def download_receipt_url(request, order_id):
    """Get direct download URL for receipt PDF"""
    try:
        order = OrderDetail.objects.get(id=order_id)
        # Verify user owns this order (via email or user account)
        if order.customer_email != request.user.email:
            return JsonResponse({"error": "Access denied"}, status=403)
        
        if not order.receipt:
            return JsonResponse({"error": "Receipt not generated yet"}, status=404)
        
        # Return the Cloudinary URL
        receipt_url = order.receipt.url
        return JsonResponse({"url": receipt_url})
    except OrderDetail.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        print(f"Receipt URL error: {e}")
        return JsonResponse({"error": "Could not get receipt URL"}, status=500)


@csrf_exempt
def payment_handler(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id   = request.POST.get('razorpay_order_id', '')
            signature  = request.POST.get('razorpay_signature', '')

            client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_SECRET_KEY))

            # Verify signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            # Update order in DB
            order = OrderDetail.objects.filter(razor_order_id=order_id).first()
            if order:
                order.razor_payment_id = payment_id
                order.status = "PAID"
                order.has_paid = True
                order.save()

                product = order.product
                product.total_sales_amount += int(order.amount)
                product.total_sales += 1
                product.save()

            # ✅ Redirect (not JSON) — UPI expects this
            return redirect(f'/payment-success/?order_id={order.id}')

        except razorpay.errors.SignatureVerificationError:
            return redirect('/payment-failed/?error=Signature verification failed')
        except Exception as e:
            return redirect(f'/payment-failed/?error={str(e)}')

    return JsonResponse({"status": "Invalid Request"}, status=400)



# JWT Auth Views

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Account created successfully'}, status=201)
        return Response(serializer.errors, status=400)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except Exception:
            return Response({'error': 'Invalid token'}, status=400)
        
class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(seller=request.user).order_by('-id')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
class ProductListView(APIView):
    permission_classes = [permissions.AllowAny]  # public, no token needed

    def get(self, request):
        products = Product.cache.get('product_list')
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]  # public, no token needed

    def get(self, request, id):
        product = get_object_or_404(Product, id=id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    
class ProductCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProductWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(seller=request.user)  # seller pulled from JWT, not request body
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ProductEditView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, id):
        product = get_object_or_404(Product, id=id)
        if product.seller != request.user:
            return Response({'error': 'Not authorized'}, status=403)
        serializer = ProductWriteSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ProductDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id):
        product = get_object_or_404(Product, id=id)
        if product.seller != request.user:
            return Response({'error': 'Not authorized'}, status=403)
        name = product.name
        product.delete()
        return Response({'message': f'{name} deleted successfully'})
    
class MyPurchasesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = OrderDetail.objects.filter(
            customer_email=request.user.email,
            status="PAID"
        ).order_by('-created_on')
        serializer = OrderDetailSerializer(orders, many=True)
        return Response(serializer.data)


class SalesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = OrderDetail.objects.filter(
            product__seller=request.user,
            status="PAID"
        )

        total_sales = orders.aggregate(Sum('amount'))

        last_year = datetime.date.today() - datetime.timedelta(days=365)
        yearly_sales = orders.filter(created_on__gt=last_year).aggregate(Sum('amount'))

        last_month = datetime.date.today() - datetime.timedelta(days=30)
        monthly_sales = orders.filter(created_on__gt=last_month).aggregate(Sum('amount'))

        last_week = datetime.date.today() - datetime.timedelta(days=7)
        weekly_sales = orders.filter(created_on__gt=last_week).aggregate(Sum('amount'))

        daily_sales_sums = list(
            orders.values('created_on__date')
            .order_by('created_on__date')
            .annotate(sum=Sum('amount'))
        )

        product_sales_sums = list(
            orders.values('product__name')
            .order_by('product__name')
            .annotate(sum=Sum('amount'))
        )

        return Response({
            'total_sales': total_sales['amount__sum'],
            'yearly_sales': yearly_sales['amount__sum'],
            'monthly_sales': monthly_sales['amount__sum'],
            'weekly_sales': weekly_sales['amount__sum'],
            'daily_sales_sums': daily_sales_sums,
            'product_sales_sums': product_sales_sums,
        })