import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField, Case, When, Value, CharField
from django.db import transaction
from datetime import datetime
from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from po_receive.models import po_receive_details
from purchase_order.models import purchase_order_list, purchase_orderdtls
from item_setup.models import items
from po_return.models import po_return_details
from po_return_receive.models import po_return_received_details
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from G_R_N_with_without.models import without_GRN, without_GRNdtl
from registrations.models import in_registrations
from . models import opening_balance, paymentsdtls
from supplier_setup.models import suppliers
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def openingBalanceManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []
    
    context = {
        'org_list': org_list,
    }

    return render(request, 'clients_transection/add_opening_balance.html', context)


# get registration list
@login_required()
def getRegistrationsListAPI(request):
    search_query = request.GET.get('search_query', '')
    org_id_wise_filter = request.GET.get('org_filter', '')

    # Initialize an empty Q object for dynamic filters
    filter_kwargs = Q()

    # Add search conditions only if search_query is not empty
    if search_query:
        filter_kwargs |= Q(full_name__icontains=search_query) | Q(customer_no__icontains=search_query) | Q(mobile_number__icontains=search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Apply filter_kwargs to the query
    reg_data = in_registrations.objects.filter(is_active=True).filter(filter_kwargs)

    data = []
    for reg in reg_data:
        data.append({
            'reg_id': reg.reg_id,
            'customer_no': reg.customer_no,
            'full_name': reg.full_name,
            'mobile_number': reg.mobile_number,
        })

    return JsonResponse({'data': data})


# registration value click to show
@login_required()
def selectRegistrationListAPI(request, reg_id):

    try:
        reg_list = get_object_or_404(in_registrations, reg_id=reg_id)

        regis_Dtls = []

        regis_Dtls.append({
            'reg_id': reg_list.reg_id,
            'customer_no': reg_list.customer_no,
            'mobile_number': reg_list.mobile_number,
            'full_name': reg_list.full_name,
            'address': reg_list.address,
            'gender': reg_list.gender,
            'marital_status': reg_list.marital_status,
            'blood_group': reg_list.blood_group,
            'dateofbirth': reg_list.dateofbirth,
        })

        context = {
            'regis_Dtls': regis_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# opening balance transaction add view
@login_required()
def saveOpBalanceTransactionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id=data.get('filter_org')
    reg_id=data.get('reg_id')
    is_debited=data.get('is_debited', False)
    is_credited=data.get('is_credited', False)
    op_amount = data.get('op_amount')
    descriptions = data.get('descriptions')

    try:
        org_instance = organizationlst.objects.get(org_id=org_id)
    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Organization not found'
        return JsonResponse(resp)

    try:
        reg_instance = in_registrations.objects.get(reg_id=reg_id)
    except in_registrations.DoesNotExist:
        resp['errmsg'] = 'Registration not found'
        return JsonResponse(resp)

    opb_trans = opening_balance(
        org_id=org_instance,
        reg_id=reg_instance,
        opb_amount=op_amount,
        is_debited=is_debited,
        is_credited=is_credited,
        descriptions=descriptions,
        ss_creator = request.user,
        ss_modifier = request.user,
    )
    opb_trans.save()

    resp = {'success': True, 'msg': 'Saved successfully'}

    return JsonResponse(resp)


@login_required()
def getOpeningBalancesAmountAPI(request):
    if request.method == "GET":
        # Get the organization and registration IDs from the query parameters
        org_id = request.GET.get('org_id')
        reg_id = request.GET.get('reg_id')

        # Filter the opening balances based on org_id and reg_id
        opening_balances = opening_balance.objects.all()

        if org_id:
            opening_balances = opening_balances.filter(org_id=org_id)

        if reg_id:
            opening_balances = opening_balances.filter(reg_id=reg_id)

        # Retrieve the values to return
        opening_balances = opening_balances.values(
            'opb_id',
            'opb_date',
            'org_id',
            'reg_id',
            'is_debited',
            'is_credited',
            'descriptions',
            'opb_amount',
        )
        
        data = list(opening_balances)  # Convert queryset to a list of dictionaries
        return JsonResponse(data, safe=False)
    

# ===================================== Reg clients payments =====================================

@login_required()
def regClientsPaymentManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []
    
    context = {
        'org_list': org_list,
    }

    return render(request, 'reg_client_payment/reg_clients_payment.html', context)

# save payment data
@login_required()
def saveregClientsPaymentTransactionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id=data.get('filter_org')
    reg_id=data.get('reg_id')
    pay_amount = data.get('pay_amount')
    descriptions = data.get('descriptions')
    pay_mode = data.get('pay_mode')
    pay_type = data.get('pay_type')
    comments = data.get('comments')
    card_info = data.get('card_info')
    pay_mob_number = data.get('pay_mob_number')
    pay_reference = data.get('pay_reference')
    bank_name = data.get('bank_name')

    try:
        org_instance = organizationlst.objects.get(org_id=org_id)
    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Organization not found'
        return JsonResponse(resp)

    try:
        reg_instance = in_registrations.objects.get(reg_id=reg_id)
    except in_registrations.DoesNotExist:
        resp['errmsg'] = 'Registration not found'
        return JsonResponse(resp)

    pay_trans = paymentsdtls(
        org_id=org_instance,
        reg_id=reg_instance,
        pay_amount=pay_amount,
        descriptions=descriptions,
        pay_mode=pay_mode,
        pay_type=pay_type,
        comments=comments,
        card_info=card_info,
        pay_mob_number=pay_mob_number,
        pay_reference=pay_reference,
        bank_name=bank_name,
        ss_creator = request.user,
        ss_modifier = request.user,
    )
    pay_trans.save()

    resp = {'success': True, 'msg': 'Saved successfully'}

    return JsonResponse(resp)

# get payment dtls
@login_required()
def getpaymentDtlsDataAPI(request):
    if request.method == "GET":
        # Get the organization and registration IDs from the query parameters
        org_id = request.GET.get('org_id')
        reg_id = request.GET.get('reg_id')

        # Filter the opening balances based on org_id and reg_id
        paymentDtls = paymentsdtls.objects.all()

        if org_id:
            paymentDtls = paymentDtls.filter(org_id=org_id)

        if reg_id:
            paymentDtls = paymentDtls.filter(reg_id=reg_id)

        # Retrieve the values to return
        paymentDtls = paymentDtls.annotate(
            creator_name=F('ss_creator__username')
        ).values(
            'pay_id',
            'pay_date',
            'card_info',
            'pay_mob_number',
            'pay_reference',
            'bank_name',
            'comments',
            'descriptions',
            'creator_name',
            'pay_amount'
        )
        
        data = list(paymentDtls)  # Convert queryset to a list of dictionaries
        return JsonResponse(data, safe=False)