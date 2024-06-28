import json
import sys
import logging
from django.shortcuts import render, redirect, HttpResponseRedirect
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from .forms import UserLoginForm
from django.contrib import messages
from collections import defaultdict
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from module_setup.models import module_type, module_list, feature_list
from user_setup.models import access_list
from organizations.models import organizationlst
from django.http import HttpResponseNotFound
from .decorators import login_required_with_timeout
from stock_list.models import stock_lists
from item_pos.models import invoice_list, invoicedtl_list, payment_list
from item_setup.models import items
from django.contrib.auth import get_user_model
User = get_user_model()


def ratelimited_view(request, exception):
    return JsonResponse({'success': False, 'errmsg': 'Too many requests. Please try again later.'}, status=429)


def user_loginManagerAPI(request):

    return render(request, 'logger/singin_form.html')

def fetch_organizations(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        # Fetch the user object
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return JsonResponse({'organizations': []})

        # Check if the user has an org_id
        if user.org_id:
            # Fetch organizations based on the user's org_id
            organizations = organizationlst.objects.filter(org_id=user.org_id).values('org_id', 'org_name')

            if organizations.exists():
                organizations_list = list(organizations)
                return JsonResponse({'organizations': organizations_list})
        
        return JsonResponse({'organizations': []})

    return JsonResponse({'error': 'Invalid request'})


logger = logging.getLogger(__name__)
@csrf_protect
@ratelimit(key='user', rate='100/m', method='POST', block=True)
def user_loginAPI(request):
    resp = {'success': False, 'errmsg': 'Invalid Username and Password. Please Try Again.'}
    present_date = datetime.now().date()
    
    if request.method == 'POST':
        logout(request)
        username = request.POST.get('username')
        password = request.POST.get('password')
        org_name = request.POST.get('org_name')
        
        # Fetch organization based on org_name
        try:
            organization = organizationlst.objects.get(org_id=org_name)
        except organizationlst.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': 'Organization not found.'})
        
        # Fetch user based on the username (case-insensitive)
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            user = None
        
        # Authenticate user with the provided password
        if user is not None and user.check_password(password):
            # Check if the user's org_id matches the organization's org_id
            if user.org_id == organization.org_id:
                # Check if the user's expiry_date is less than the present_date
                if user.expiry_date and user.expiry_date < present_date:
                    return JsonResponse({'success': False, 'errmsg': 'User account has expired. Please contact the administration.'})
                
                user.is_login_status = True
                user.save()
                
                login(request, user)
                logger.info(f"User {user.username} logged in successfully.")
                return JsonResponse({'success': True, 'msg': 'Login Successful.'})
            else:
                logger.warning(f"User {username} provided an invalid organization.")
                return JsonResponse({'success': False, 'errmsg': 'Invalid organization.'})
        else:
            logger.warning(f"Invalid login attempt for username: {username}")
            return JsonResponse({'success': False, 'errmsg': 'Invalid Username and Password. Please Try Again.'})
    
    return JsonResponse(resp)


@login_required_with_timeout
def main_dashboard(request):
    active_access_list_data = []

    if request.user.is_authenticated:
        access_list_data = access_list.objects.filter(
            user_id=request.user,
            feature_id__is_active=True,
            feature_id__module_id__is_active=True,
            feature_id__module_id__module_id2feature_list__is_active=True,
            feature_id__type_id__is_active=True,  # Check is_active on the related module_type
            feature_id__feature_type="Form",
        ).select_related(
            'feature_id__type_id',  # Select the related module_type
            'feature_id__module_id',  # Select the related module_list
        )

        active_access_list_data = access_list_data.filter(
            feature_id__is_active=True,
            feature_id__module_id__is_active=True,
            feature_id__module_id__module_id2feature_list__is_active=True,
            feature_id__type_id__is_active=True,  # Apply the same is_active filter here
        ).distinct()

    context = {
        'active_access_list_data': active_access_list_data,
    }

    return render(request, 'main_dashboard/main_dashboard.html', context)


@login_required()
def logoutuser(request):
    # Fetch the current user
    current_user = request.user

    # Update the user's login status to False upon logout
    if current_user.is_authenticated:
        current_user.is_login_status = False
        current_user.save()

    logout(request)
    messages.success(request, 'Logout successfully!')
    return redirect('login')

@login_required()
def statisticsManagerAPI(request):

    context = {
        
    }

    return render(request, 'statistics/statistics.html', context)

@login_required()
def get_total_itemsManagerAPI(request):

    total_items_count = items.objects.filter(is_active=True).count()

    data = {'total_items_count': total_items_count}

    return JsonResponse(data)

@login_required()
def getConsumptionManagerAPI(request):
    static_start = 0
    static_end = 0
    if request.method == "POST":
        today = date.today()
        sales_total_qty = 0

        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()
        
        # Fetch all invoices for the specified date range
        invoices = invoice_list.objects.filter(invoice_date__range=(static_start, static_end)).all()
        
        # Calculate total sales quantity for each invoice
        for inv in invoices:
            invoice_details = invoicedtl_list.objects.filter(inv_id=inv).all()
            total_qty = invoice_details.aggregate(
                total_qty=Sum(ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField()))
            )['total_qty'] or 0
            
            # Accumulate the total sales quantity
            sales_total_qty += total_qty

        data = {'sales_total_qty': sales_total_qty}

        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)

@login_required()
def getSalesAmountManagerAPI(request):
    static_start = 0
    static_end = 0

    # Initialize the grand total
    all_total_net_bill = 0

    if request.method == "POST":

        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()
        
        # Fetch all invoices for today
        invoices = invoice_list.objects.filter(invoice_date__range=(static_start, static_end)).all()
        invoice_details = invoicedtl_list.objects.all()
        
        # Calculate total sales quantity for each invoice
        for invoice in invoices:
            details = invoice_details.filter(inv_id=invoice).all()

            # Initialize invoice-wise totals
            grand_total = 0
            grand_total_dis = 0
            grand_vat_tax = 0
            grand_cancel_amt = 0
            grand_total_gross_dis = 0
            total_discount_sum = 0

            # Item rate over invoice items
            item_total = sum(detail.sales_rate * detail.qty for detail in details)
            grand_total += item_total

            # Discount calculation
            item_w_dis = sum(((detail.item_w_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)

            grand_total_dis += item_w_dis
            grand_total_dis = round(grand_total_dis, 2)

            total_gross_dis = sum(((detail.gross_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)

            grand_total_gross_dis += total_gross_dis
            grand_total_gross_dis = round(grand_total_gross_dis, 2)

            total_discount_sum = grand_total_dis + grand_total_gross_dis

            # VAT tax calculation
            item_wise_total_vat_tax = sum(((detail.gross_vat_tax / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)

            grand_vat_tax += item_wise_total_vat_tax
            grand_vat_tax = round(grand_vat_tax, 2)

            # Cancel amount calculation
            total_item_cancel_amt = sum(detail.sales_rate * detail.is_cancel_qty for detail in details)
            grand_cancel_amt += total_item_cancel_amt

            # Calculate total net bill for this invoice
            total_net_bill = ((grand_total + grand_vat_tax) - (total_discount_sum + grand_cancel_amt))
            total_net_bill = round(total_net_bill, 0)

            all_total_net_bill += total_net_bill

        data = {'sales_total_amt': all_total_net_bill}

        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)

@login_required()
def getCollectionAmtManagerAPI(request):
    static_start = 0
    static_end = 0
    if request.method == "POST":
        today = date.today()
        net_grand_collection = Decimal('0.0')

        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()
        
        payments = payment_list.objects.filter(pay_date__range=(static_start, static_end)).all()

        collections_by_inv_id = defaultdict(lambda: {
            'total_collection_amt': Decimal('0.0'),
            'total_due_collection_amt': Decimal('0.0'),
            'total_refund_collection_amt': Decimal('0.0')
        })

        for paymentData in payments:
            pay_amt = Decimal(paymentData.pay_amt)
            if paymentData.collection_mode == "1":
                collections_by_inv_id[paymentData.inv_id]['total_collection_amt'] += pay_amt
            elif paymentData.collection_mode == "2":
                collections_by_inv_id[paymentData.inv_id]['total_due_collection_amt'] += pay_amt
            elif paymentData.collection_mode == "3":
                collections_by_inv_id[paymentData.inv_id]['total_refund_collection_amt'] += pay_amt

        for inv_id, collections in collections_by_inv_id.items():
            grand_collection = (collections['total_collection_amt'] + collections['total_due_collection_amt'] - collections['total_refund_collection_amt'])
            net_grand_collection += grand_collection

        net_grand_collection = round(net_grand_collection, 0)
        data = {'net_grand_collection': str(net_grand_collection)}

        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)


@login_required()
def storeWiseStockQtyManagerAPI(request):
    store_quantities = stock_lists.objects.filter(is_approved=True).values('store_id__store_name').annotate(total_quantity=Sum('stock_qty'))

    labels = []
    sizes = []

    for store_quantity in store_quantities:
        store_name = store_quantity['store_id__store_name']
        quantity = store_quantity['total_quantity']
        labels.append(store_name)
        sizes.append(quantity)

        invoice_details = invoicedtl_list.objects.filter(store_id__store_name=store_name).all()
        sales_total_qty = invoice_details.aggregate(
            sales_total_qty=Sum(ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField()))
        )['sales_total_qty'] or 0

        total_stock_qty = quantity - sales_total_qty
        sizes[-1] = total_stock_qty  # Update sizes list with the remaining stock quantity

    data = {
        'labels': labels,
        'sizes': sizes,
    }

    return JsonResponse(data)


@login_required()
def getDetailsSalesManagerAPI(request):
    static_start = 0
    static_end = 0
    if request.method == "POST":
        today = datetime.now().date()
        invoice_timestamps = defaultdict(set)  # Store timestamps for each inv_id
        details_sales_amt = []

        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()

        # Fetch all invoices for today
        invoices = invoice_list.objects.filter(invoice_date__range=(static_start, static_end)).all()

        # Calculate total sales quantity for each invoice
        for inv in invoices:
            invoice_details = invoicedtl_list.objects.filter(inv_id=inv).all()
            total_sales_amt = 0
            timestamps = set()  # Store timestamps for the current inv_id
            for detail in invoice_details:
                # Convert the UTC time to local time zone
                local_time = timezone.localtime(detail.ss_created_on)
                
                # Retrieve timestamp_field and format it to display only time
                timestamp = local_time.strftime('%I.%M %p')  # Format time as '12.15 AM'
                timestamps.add(timestamp)

                # Calculate sales amount per detail and accumulate in total_sales_amt
                sales_amt = (detail.qty - detail.is_cancel_qty) * detail.sales_rate
                total_sales_amt += sales_amt

            # Store timestamps for the current inv_id
            invoice_timestamps[inv.inv_id] = timestamps
            
            # Append total sales amount for the invoice after processing all details
            details_sales_amt.append(total_sales_amt)

        # Flatten the timestamps for each inv_id
        timestamps = [timestamp for timestamps_set in invoice_timestamps.values() for timestamp in timestamps_set]

        data = {'timestamps': timestamps, 'details_sales_amt': details_sales_amt}

        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)


@login_required()
def getItemWiseSalesManagerAPI(request):
    if request.method == "POST":
        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()

        # Fetch all invoices for the specified date range
        invoices = invoice_list.objects.filter(invoice_date__range=(static_start, static_end)).all()

        # Calculate total sales quantity for each item_id across all invoices
        item_wise_sales = defaultdict(float)

        for inv in invoices:
            invoice_details = invoicedtl_list.objects.filter(inv_id=inv).all()
            for detail in invoice_details:
                item_id = detail.item_id.item_name  # Get the item_id for the detail
                sales_amt = (detail.qty - detail.is_cancel_qty) * detail.sales_rate
                item_wise_sales[item_id] += sales_amt  # Accumulate sales amount for each item_id

        data = {'item_wise_sales': dict(item_wise_sales)}
        print(data)
        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)

# get user org information
@login_required()
def getUserInfoAPI(request):
    user = request.user

    # Access user data
    user_data = {
        'user_id': user.user_id,
        'org_id': user.org_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'designation': user.designation,
    }

    # Fetch organization information
    try:
        organization = organizationlst.objects.get(org_id=user.org_id)
        org_data = {
            'org_id': organization.org_id,
            'org_name': organization.org_name,
            'address': organization.address,
            'phone': organization.phone,
            'hotline': organization.hotline,
            'fax': organization.fax,
            'email': organization.email,
            'website': organization.website,
            'org_logo': organization.org_logo.url if organization.org_logo else None,  # Get the URL of the image
        }
    except organizationlst.DoesNotExist:
        org_data = {
            'org_id': None,
            'org_name': None,
            'address': None,
            'phone': None,
            'hotline': None,
            'fax': None,
            'email': None,
            'website': None,
            'org_logo': None,
        }

    # Combine user and organization data
    result_data = {**user_data, **org_data}

    return JsonResponse(result_data, encoder=DjangoJSONEncoder)

# ======================================testing===================================
def testLogin(request):

    return render(request, 'logger/test.html')