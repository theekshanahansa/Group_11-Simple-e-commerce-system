from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm


def home(request):
    return render(request, 'shop/home.html')


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
            auth_login(request, user)
            return redirect('product_list')  # Redirect to product list after successful login
        else:
            return render(request, 'shop/login.html', {'error': 'Invalid username or password'})
    return render(request, 'shop/login.html')


# User logout view
def logout_view(request):
    logout(request)
    return redirect('product_list')


# View to list all products
def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})


# View to list products by category
def product_by_category(request, category_id):
    products = Product.objects.filter(category_id=category_id)
    return render(request, 'shop/product_list.html', {'products': products})


# View to show product details
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


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


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_confirmation.html', {'order': order})


# View to handle checkout
@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    if request.method == 'POST':
        order = Order.objects.create(user=request.user, total_price=0)
        total_price = 0
        for item in CartItem.objects.filter(cart=cart):
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity,
                                     price=item.product.price)
            total_price += item.product.price * item.quantity
            item.delete()
        order.total_price = total_price
        order.save()
        cart.delete()
        return redirect('order_confirmation', order_id=order.id)
    return render(request, 'shop/checkout.html')


# View to show order confirmation
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_confirmation.html', {'order': order})
