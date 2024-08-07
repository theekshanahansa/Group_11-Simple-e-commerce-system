from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from django.contrib.auth import login
from .forms import UserRegistrationForm
from .models import Category, Product
import json
import os
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cart, Order, OrderItem, Customer
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    featured_products = Product.objects.filter(id__in=[8, 12, 40, 13, ]).union(Product.objects.all()[:0])
    return render(request, 'shop/home.html', {'featured_products': featured_products})


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('home')  # Redirect to a success page
    else:
        form = UserRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})


# User login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home or another page
        else:
            # Handle invalid login
            return render(request, 'shop/login.html', {'error': 'Invalid username or password.'})
    else:
        return render(request, 'shop/login.html')


# User logout view
def logout_view(request):
    logout(request)
    return redirect('home')


def product_list(request):
    category = request.GET.get('category', 'all')
    price = request.GET.get('price', 60000)

    products = Product.objects.all()

    if category and category != 'all':
        products = products.filter(category__name=category)

    if price:
        max_price = int(price)
        products = products.filter(price__lte=max_price)

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
    }

    return render(request, 'shop/product_list.html', context)


# View to list products by category
def product_by_category(request, category_id):
    products = Product.objects.filter(category_id=category_id)
    return render(request, 'shop/product_list.html', {'products': products})


# View to show product details
# File to store reviews
REVIEWS_FILE = 'reviews.json'


def add_review(request, product_id):
    if request.method == 'POST':
        review = request.POST.get('review')
        if review:
            reviews = load_reviews()
            product_reviews = reviews.get(str(product_id), [])
            product_reviews.append(review)
            reviews[str(product_id)] = product_reviews
            save_reviews(reviews)
            messages.success(request, 'Review submitted successfully.')
    return redirect('product_detail', product_id=product_id)


def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_reviews(reviews):
    with open(REVIEWS_FILE, 'w') as file:
        json.dump(reviews, file)


def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:3]

    reviews = load_reviews().get(str(product_id), [])

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
    })


# View to add a product to the cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('view_cart')


# View to remove a product from the cart
@login_required
def remove_from_cart(request, product_id):
    cart = Cart.objects.get(user=request.user)
    cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
    cart_item.delete()
    return redirect('view_cart')


# View to show the cart
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    return render(request, 'shop/cart.html', {'cart_items': cart_items})


# View to handle checkout
@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = None

    customer, created = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        address = request.POST['address']
        payment_method = request.POST['payment-method']

        # Save the new address if it's different from the current one
        if address != customer.shipping_address:
            customer.shipping_address = address
            customer.save()

        # Create an order
        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total_price()
        )

        # Create order items from cart items
        for item in cart.cartitem_set.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # Clear the cart
        cart.cartitem_set.all().delete()

        # Redirect to order confirmation page
        return redirect('order_confirmation', order_id=order.id)

    context = {
        'cart': cart,
        'user': request.user,
        'address': customer.shipping_address
    }
    return render(request, 'shop/checkout.html', context)


# View to show order confirmation
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Calculate total price for each order item
    for item in order.orderitem_set.all():
        item.total = item.quantity * item.price  # Calculate total price for the item

    context = {
        'order': order,
    }
    return render(request, 'shop/order_confirmation.html', context)


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'shop/products_by_category.html', {'category': category, 'products': products})


def about_us(request):
    return render(request, 'shop/about.html')


def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # For now, just print it to the console (for demonstration purposes)
        print(f"Subscribed email: {email}")
        return HttpResponse("Thank you for subscribing!")
    return redirect('home')


