from django.shortcuts import render, redirect, reverse, get_object_or_404
from . import forms, models
from django.http import HttpResponseRedirect, HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings

def home_view(request):
    products = models.Product.objects.all()
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'ecom/index.html', {'products': products, 'product_count_in_cart': product_count_in_cart})

#for showing login button for admin(by sumit)
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')

def customer_signup_view(request):
    userForm = forms.CustomerUserForm()
    customerForm = forms.CustomerForm()
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerForm(request.POST, request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customer = customerForm.save(commit=False)
            customer.user = user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('customerlogin')
    return render(request, 'ecom/customersignup.html', context=mydict)

#-----------for checking user is customer
def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()

#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,CUSTOMER
def afterlogin_view(request):
    if is_customer(request.user):
        return redirect('customer-home')
    else:
        return redirect('admin-dashboard')

#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    # for cards on dashboard
    customercount = models.Customer.objects.all().count()
    productcount = models.Product.objects.all().count()
    ordercount = models.Orders.objects.all().count()

    # for recent order tables
    orders = models.Orders.objects.all()
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_by = models.Customer.objects.all().filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)

    mydict = {
        'customercount': customercount,
        'productcount': productcount,
        'ordercount': ordercount,
        'data': zip(ordered_products, ordered_bys, orders),
    }
    return render(request, 'ecom/admin_dashboard.html', context=mydict)

# admin view customer table
@login_required(login_url='adminlogin')
def view_customer_view(request):
    customers = models.Customer.objects.all()
    return render(request, 'ecom/view_customer.html', {'customers': customers})

# admin delete customer
@login_required(login_url='adminlogin')
def delete_customer_view(request, pk):
    customer = models.Customer.objects.get(id=pk)
    user = models.User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return redirect('view-customer')

@login_required(login_url='adminlogin')
def update_customer_view(request, pk):
    customer = models.Customer.objects.get(id=pk)
    user = models.User.objects.get(id=customer.user_id)
    userForm = forms.CustomerUserForm(instance=user)
    customerForm = forms.CustomerForm(request.FILES, instance=customer)
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('view-customer')
    return render(request, 'ecom/admin_update_customer.html', context=mydict)

# admin view the product
@login_required(login_url='adminlogin')
def admin_products_view(request):
    products = models.Product.objects.all()
    return render(request, 'ecom/admin_products.html', {'products': products})

# admin add product by clicking on floating button
@login_required(login_url='adminlogin')
def admin_add_product_view(request):
    productForm = forms.ProductForm()
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect('admin-products')
    return render(request, 'ecom/admin_add_products.html', {'productForm': productForm})

@login_required(login_url='adminlogin')
def delete_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    product.delete()
    return redirect('admin-products')

@login_required(login_url='adminlogin')
def update_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    productForm = forms.ProductForm(instance=product)
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid():
            productForm.save()
            return redirect('admin-products')
    return render(request, 'ecom/admin_update_product.html', {'productForm': productForm})

@login_required(login_url='adminlogin')
def admin_view_booking_view(request):
    orders = models.Orders.objects.all()
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_by = models.Customer.objects.all().filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)
    return render(request, 'ecom/admin_view_booking.html', {'data': zip(ordered_products, ordered_bys, orders)})

@login_required(login_url='adminlogin')
def delete_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    order.delete()
    return redirect('admin-view-booking')

# for changing status of order (pending,delivered...)
@login_required(login_url='adminlogin')
def update_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    orderForm = forms.OrderForm(instance=order)
    if request.method == 'POST':
        orderForm = forms.OrderForm(request.POST, instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect('admin-view-booking')
    return render(request, 'ecom/update_order.html', {'orderForm': orderForm})

# admin view the feedback
@login_required(login_url='adminlogin')
def view_feedback_view(request):
    feedbacks = models.Feedback.objects.all().order_by('-id')
    return render(request, 'ecom/view_feedback.html', {'feedbacks': feedbacks})

#---------------------------------------------------------------------------------
#------------------------ PUBLIC CUSTOMER RELATED VIEWS START ---------------------
#---------------------------------------------------------------------------------
def search_view(request):
    # whatever user write in search box we get in query
    query = request.GET['query']
    products = models.Product.objects.all().filter(name__icontains=query)
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # word variable will be shown in html when user click on search button
    word = "Searched Result :"

    if request.user.is_authenticated:
        return render(request, 'ecom/customer_home.html', {'products': products, 'word': word, 'product_count_in_cart': product_count_in_cart})
    return render(request, 'ecom/index.html', {'products': products, 'word': word, 'product_count_in_cart': product_count_in_cart})

# any one can add product to cart, no need of signin
def add_to_cart_view(request, pk):
    products = models.Product.objects.all()

    #for cart counter, fetching products ids added by customer from cookies
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 1

    response = render(request, 'ecom/index.html', {'products': products, 'product_count_in_cart': product_count_in_cart})

    #adding product id to cookies
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids == "":
            product_ids = str(pk)
        else:
            product_ids = product_ids + '|' + str(pk)
        response.set_cookie('product_ids', product_ids)
    else:
        response.set_cookie('product_ids', pk)
    product = models.Product.objects.get(id=pk)
    messages.info(request, product.name + ' added to cart successfully!')
    return response

# for checkout of cart
def cart_view(request):
    #for cart counter
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # fetching product details from db whose id is present in cookie
    products = None
    total = 0
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)

            #for total price shown in cart
            for p in products:
                total = total + p.price

    return render(request, 'ecom/cart.html', {'products': products, 'total': total, 'product_count_in_cart': product_count_in_cart})

def remove_from_cart_view(request, pk):
    # for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # removing product id from cookie
    total = 0
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_id_in_cart = product_ids.split('|')
        product_id_in_cart = list(set(product_id_in_cart))
        product_id_in_cart.remove(str(pk))
        products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        # for total price shown in cart after removing product
        for p in products:
            total = total + p.price

        #  for update coookie value after removing product id in cart
        value = ""
        for i in range(len(product_id_in_cart)):
            if i == 0:
                value = value + product_id_in_cart[0]
            else:
                value = value + "|" + product_id_in_cart[i]
        response = render(request, 'ecom/cart.html', {'products': products, 'total': total, 'product_count_in_cart': product_count_in_cart})
        if value == "":
            response.set_cookie('product_ids', value)
        else:
            response.set_cookie('product_ids', value)
        return response

@login_required(login_url='customerlogin')
def customer_home_view(request):
    products = models.Product.objects.all()

    # for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    return render(request, 'ecom/customer_home.html', {'products': products, 'product_count_in_cart': product_count_in_cart})

# shipping address before plcaing order
@login_required(login_url='customerlogin')
def customer_address_view(request):
    product_in_cart = False
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_in_cart = True
    #for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            email = addressForm.cleaned_data['Email']
            mobile = addressForm.cleaned_data['Mobile']
            address = addressForm.cleaned_data['Address']

            #for showing total price on payment page....accessing id from cookies
            total = 0
            if 'product_ids' in request.COOKIES:
                product_ids = request.COOKIES['product_ids']
                if product_ids != "":
                    product_id_in_cart = product_ids.split('|')
                    products = models.Product.objects.all().filter(id__in=product_id_in_cart)

                    # for total price shown in cart
                    for p in products:
                        total = total + p.price

            response = render(request, 'ecom/payment.html', {'total': total})
            response.set_cookie('email', email)
            response.set_cookie('mobile', mobile)
            response.set_cookie('address', address)
            return response

    return render(request, 'ecom/customer_address.html', {'addressForm': addressForm, 'product_in_cart': product_in_cart, 'product_count_in_cart': product_count_in_cart})

@login_required(login_url='customerlogin')
def payment_success_view(request):
    #for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    customer = models.Customer.objects.get(user_id=request.user.id)
    products = None
    email = None
    mobile = None
    address = None
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        # for storing email, mobile and address in order model for sending to admin
        if 'email' in request.COOKIES:
            email = request.COOKIES['email']
        if 'mobile' in request.COOKIES:
            mobile = request.COOKIES['mobile']
        if 'address' in request.COOKIES:
            address = request.COOKIES['address']

        for product in products:
            models.Orders.objects.get_or_create(customer=customer, product=product, status='Pending')
        response = render(request, 'ecom/payment_success.html')
        response.delete_cookie('product_ids')
        response.delete_cookie('email')
        response.delete_cookie('mobile')
        response.delete_cookie('address')

        # send a notification email to customer
        send_mail(
            'Order Placed Successfully',
            f'Dear {customer.user.first_name},\n\nYour order has been placed successfully. You will receive your products soon.\n\nThank you for shopping with us!',
            settings.EMAIL_HOST_USER,
            [customer.user.email],
            fail_silently=False,
        )

        # send a notification email to admin
        send_mail(
            'New Order Placed',
            f'A new order has been placed by {customer.user.first_name} {customer.user.last_name}.\n\nProducts Ordered:\n\n' + 
            '\n'.join([product.name for product in products]) +
            f'\n\nDelivery Address:\n{address}\n\nContact Information:\nEmail: {email}\nPhone: {mobile}',
            settings.EMAIL_HOST_USER,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        return response

    return HttpResponseRedirect('customer-home')

@login_required(login_url='customerlogin')
def my_order_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Orders.objects.all().filter(customer_id=customer)
    ordered_products = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_products.append(ordered_product)

    return render(request, 'ecom/my_order.html', {'data': zip(ordered_products, orders)})

@login_required(login_url='customerlogin')
def my_profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    user = models.User.objects.get(id=customer.user_id)
    userForm = forms.CustomerUserForm(instance=user)
    customerForm = forms.CustomerForm(request.FILES, instance=customer)
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, request.FILES, instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('my-profile')
    return render(request, 'ecom/my_profile.html', context=mydict)

@login_required(login_url='customerlogin')
def feedback_view(request):
    feedbackForm = forms.FeedbackForm()
    if request.method == 'POST':
        feedbackForm = forms.FeedbackForm(request.POST)
        if feedbackForm.is_valid():
            feedbackForm.save()
            return redirect('customer-home')
    return render(request, 'ecom/feedback.html', {'feedbackForm': feedbackForm})

#---------------------------------------------------------------------------------
#------------------------ AUTO RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------

def autos_list_view(request):
    autos = models.Auto.objects.all()
    return render(request, 'ecom/autos_list.html', {'autos': autos})

def auto_detail_view(request, pk):
    auto = get_object_or_404(models.Auto, pk=pk)
    return render(request, 'ecom/auto_detail.html', {'auto': auto})

@login_required(login_url='customerlogin')
def add_auto_to_cart_view(request, pk):
    response = HttpResponseRedirect('/cart')
    if 'auto_ids' in request.COOKIES:
        auto_ids = request.COOKIES['auto_ids']
        if auto_ids == "":
            auto_ids = str(pk)
        else:
            auto_ids = auto_ids + '|' + str(pk)
        response.set_cookie('auto_ids', auto_ids)
    else:
        response.set_cookie('auto_ids', pk)
    auto = models.Auto.objects.get(id=pk)
    messages.info(request, auto.name + ' added to cart successfully!')
    return response

def cart_view(request):
    #for cart counter
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # fetching product details from db whose id is present in cookie
    products = None
    total = 0
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)

            #for total price shown in cart
            for p in products:
                total = total + p.price

    # fetching auto details from db whose id is present in cookie
    autos = None
    if 'auto_ids' in request.COOKIES:
        auto_ids = request.COOKIES['auto_ids']
        if auto_ids != "":
            auto_id_in_cart = auto_ids.split('|')
            autos = models.Auto.objects.all().filter(id__in=auto_id_in_cart)

            #for total price shown in cart
            for a in autos:
                total = total + a.price

    return render(request, 'ecom/cart.html', {'products': products, 'autos': autos, 'total': total, 'product_count_in_cart': product_count_in_cart})

def remove_from_cart_view(request, pk):
    # for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # removing product id from cookie
    total = 0
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_id_in_cart = product_ids.split('|')
        product_id_in_cart = list(set(product_id_in_cart))
        product_id_in_cart.remove(str(pk))
        products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        # for total price shown in cart after removing product
        for p in products:
            total = total + p.price

        #  for update coookie value after removing product id in cart
        value = ""
        for i in range(len(product_id_in_cart)):
            if i == 0:
                value = value + product_id_in_cart[0]
            else:
                value = value + "|" + product_id_in_cart[i]
        response = render(request, 'ecom/cart.html', {'products': products, 'total': total, 'product_count_in_cart': product_count_in_cart})
        if value == "":
            response.set_cookie('product_ids', value)
        else:
            response.set_cookie('product_ids', value)
        return response

    # removing auto id from cookie
    if 'auto_ids' in request.COOKIES:
        auto_ids = request.COOKIES['auto_ids']
        auto_id_in_cart = auto_ids.split('|')
        auto_id_in_cart = list(set(auto_id_in_cart))
        auto_id_in_cart.remove(str(pk))
        autos = models.Auto.objects.all().filter(id__in=auto_id_in_cart)
        # for total price shown in cart after removing auto
        for a in autos:
            total = total + a.price

        #  for update coookie value after removing auto id in cart
        value = ""
        for i in range(len(auto_id_in_cart)):
            if i == 0:
                value = value + auto_id_in_cart[0]
            else:
                value = value + "|" + auto_id_in_cart[i]
        response = render(request, 'ecom/cart.html', {'autos': autos, 'total': total, 'product_count_in_cart': product_count_in_cart})
        if value == "":
            response.set_cookie('auto_ids', value)
        else:
            response.set_cookie('auto_ids', value)
        return response

    return HttpResponseRedirect('cart')

@login_required(login_url='customerlogin')
def customer_home_view(request):
    products = models.Product.objects.all()
    autos = models.Auto.objects.all()

    # for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    return render(request, 'ecom/customer_home.html', {'products': products, 'autos': autos, 'product_count_in_cart': product_count_in_cart})

# shipping address before placing order
@login_required(login_url='customerlogin')
def customer_address_view(request):
    product_in_cart = False
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_in_cart = True
    #for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            email = addressForm.cleaned_data['Email']
            mobile = addressForm.cleaned_data['Mobile']
            address = addressForm.cleaned_data['Address']

            #for showing total price on payment page....accessing id from cookies
            total = 0
            if 'product_ids' in request.COOKIES:
                product_ids = request.COOKIES['product_ids']
                if product_ids != "":
                    product_id_in_cart = product_ids.split('|')
                    products = models.Product.objects.all().filter(id__in=product_id_in_cart)

                    # for total price shown in cart
                    for p in products:
                        total = total + p.price

            if 'auto_ids' in request.COOKIES:
                auto_ids = request.COOKIES['auto_ids']
                if auto_ids != "":
                    auto_id_in_cart = auto_ids.split('|')
                    autos = models.Auto.objects.all().filter(id__in=auto_id_in_cart)

                    # for total price shown in cart
                    for a in autos:
                        total = total + a.price

            response = render(request, 'ecom/payment.html', {'total': total})
            response.set_cookie('email', email)
            response.set_cookie('mobile', mobile)
            response.set_cookie('address', address)
            return response

    return render(request, 'ecom/customer_address.html', {'addressForm': addressForm, 'product_in_cart': product_in_cart, 'product_count_in_cart': product_count_in_cart})

@login_required(login_url='customerlogin')
def payment_success_view(request):
    #for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    customer = models.Customer.objects.get(user_id=request.user.id)
    products = None
    autos = None
    email = None
    mobile = None
    address = None
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        # for storing email, mobile and address in order model for sending to admin
        if 'email' in request.COOKIES:
            email = request.COOKIES['email']
        if 'mobile' in request.COOKIES:
            mobile = request.COOKIES['mobile']
        if 'address' in request.COOKIES:
            address = request.COOKIES['address']

        for product in products:
            models.Orders.objects.get_or_create(customer=customer, product=product, status='Pending')

    if 'auto_ids' in request.COOKIES:
        auto_ids = request.COOKIES['auto_ids']
        if auto_ids != "":
            auto_id_in_cart = auto_ids.split('|')
            autos = models.Auto.objects.all().filter(id__in=auto_id_in_cart)
        for auto in autos:
            models.Orders.objects.get_or_create(customer=customer, auto=auto, status='Pending')

    response = render(request, 'ecom/payment_success.html')
    response.delete_cookie('product_ids')
    response.delete_cookie('auto_ids')
    response.delete_cookie('email')
    response.delete_cookie('mobile')
    response.delete_cookie('address')

    # send a notification email to customer
    send_mail(
        'Order Placed Successfully',
        f'Dear {customer.user.first_name},\n\nYour order has been placed successfully. You will receive your products soon.\n\nThank you for shopping with us!',
        settings.EMAIL_HOST_USER,
        [customer.user.email],
        fail_silently=False,
    )

    # send a notification email to admin
    send_mail(
        'New Order Placed',
        f'A new order has been placed by {customer.user.first_name} {customer.user.last_name}.\n\nProducts Ordered:\n\n' + 
        '\n'.join([product.name for product in products]) +
        f'\n\nAutos Ordered:\n\n' + 
        '\n'.join([auto.name for auto in autos]) +
        f'\n\nDelivery Address:\n{address}\n\nContact Information:\nEmail: {email}\nPhone: {mobile}',
        settings.EMAIL_HOST_USER,
        [settings.ADMIN_EMAIL],
        fail_silently=False,
    )

    return response

@login_required(login_url='customerlogin')
def my_order_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Orders.objects.all().filter(customer_id=customer)
    ordered_products = []
    ordered_autos = []
    for order in orders:
        if order.product:
            ordered_product = models.Product.objects.all().filter(id=order.product.id)
            ordered_products.append(ordered_product)
        if order.auto:
            ordered_auto = models.Auto.objects.all().filter(id=order.auto.id)
            ordered_autos.append(ordered_auto)

    return render(request, 'ecom/my_order.html', {'data': zip(ordered_products, ordered_autos, orders)})

@login_required(login_url='customerlogin')
def my_profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    user = models.User.objects.get(id=customer.user_id)
    userForm = forms.CustomerUserForm(instance=user)
    customerForm = forms.CustomerForm(request.FILES, instance=customer)
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, request.FILES, instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('my-profile')
    return render(request, 'ecom/my_profile.html', context=mydict)

@login_required(login_url='customerlogin')
def feedback_view(request):
    feedbackForm = forms.FeedbackForm()
    if request.method == 'POST':
        feedbackForm = forms.FeedbackForm(request.POST)
        if feedbackForm.is_valid():
            feedbackForm.save()
            return redirect('customer-home')
    return render(request, 'ecom/feedback.html', {'feedbackForm': feedbackForm})

#---------------------------------------------------------------------------------
#------------------------ AUTO RELATED VIEWS END --------------------------------
#---------------------------------------------------------------------------------
