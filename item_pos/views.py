import sys
import json
from num2words import num2words
from datetime import date, datetime
from pickle import FALSE
from django.db.models import Q, F, Sum, Prefetch, ExpressionWrapper, fields, FloatField
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import models
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from stock_list.models import stock_lists
from item_setup.models import item_supplierdtl, items
from store_setup.models import store
from organizations.models import branchslist, organizationlst
from b2b_clients_management.models import b2b_client_item_rates
from stock_list.stock_qty import get_available_qty
from drivers_setup.models import drivers_list
from supplier_setup.models import suppliers
from . models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def item_posAPI(request):
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

    # ==============================================================
    storeData = store.objects.filter(is_pos_report=True).all()

    # **************last invoice print*****************
    # last id query
    sales = invoice_list.objects.filter(is_cancel='0').order_by('-inv_id')[:1][::-1]
    sale_data = []
    for sale in sales:
        data = {}
        for field in sale._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(sale, field.name)

        sale_data.append(data)

    context_pos = {
        'org_list': org_list,
        'storeData': storeData,
        'sale_data': sale_data,
    }
    return render(request, 'item_pos/item_pos.html', context_pos)


@login_required()
def get_item_listAPI(request):
    selected_store_id = request.GET.get('store_id')
    selected_supplier_id = request.GET.get('filter_suppliers')
    filter_org = request.GET.get('org_id')
    b2b_client_supp = request.GET.get('b2b_client_supp_id')
    search_query = request.GET.get('query', '')  # Get the search query
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 100))  # Default page size is 100

    cache_key = f'item_list_{selected_store_id}_{selected_supplier_id}_{filter_org}_{b2b_client_supp}_{search_query}_{page_number}_{page_size}'
    cached_response = cache.get(cache_key)
    if cached_response:
        return JsonResponse(cached_response)

    try:
        # Fetch supplier details only if supplier_id filter is not 1
        if selected_supplier_id and selected_supplier_id != '1':
            supplier_qs = item_supplierdtl.objects.filter(supplier_id=selected_supplier_id).select_related('supplier_id').only('supplier_id', 'supplier_id__supplier_name')
        else:
            supplier_qs = item_supplierdtl.objects.select_related('supplier_id').only('supplier_id', 'supplier_id__supplier_name')

        stock_qs = stock_lists.objects.filter(store_id=selected_store_id).select_related('store_id').only('store_id', 'store_id__store_name', 'stock_qty')

        # Base query for items with necessary related fields and prefetches
        search_filters = Q(item_name__icontains=search_query) | Q(item_no__icontains=search_query) | Q(item_id__icontains=search_query)
        
        item_data_query = items.objects.filter(
            Q(is_active=True),
            Q(org_id=filter_org),
            search_filters,
        ).select_related('type_id', 'item_uom_id').only(
            'item_id', 'item_no', 'item_name', 'sales_price', 'type_id__type_name', 'item_uom_id__item_uom_name'
        ).prefetch_related(
            Prefetch('item_supplierdtl_set', queryset=supplier_qs, to_attr='prefetched_supplierdtl'),
            Prefetch('item_id2stock_lists', queryset=stock_qs, to_attr='prefetched_stock')
        )

        # Apply supplier filter directly on item_data_query
        if selected_supplier_id and selected_supplier_id != '1':
            item_data_query = item_data_query.filter(item_supplierdtl__supplier_id=selected_supplier_id)

        # Paginate the query
        paginator = Paginator(item_data_query, page_size)
        page_obj = paginator.get_page(page_number)

        # Fetch the item data for the current page
        item_data = list(page_obj)

        # Fetch b2b_client_item_rates separately
        b2b_client_rates = {}
        if b2b_client_supp:
            b2b_client_rates = {
                rate.item_id_id: rate.b2b_client_rate
                for rate in b2b_client_item_rates.objects.filter(
                    org_id=filter_org,
                    supplier_id=b2b_client_supp,
                    item_id__in=[item.item_id for item in item_data]
                ).only('item_id', 'b2b_client_rate')
            }

        # Build the serialized response
        serialized_data = []
        for item in item_data:
            supplier_data = item.prefetched_supplierdtl[0] if item.prefetched_supplierdtl else None
            b2b_client_item_rate = b2b_client_rates.get(item.item_id, None)
            available_qty = get_available_qty(item, selected_store_id, filter_org)
            stock_details = item.prefetched_stock[0] if item.prefetched_stock else None

            sales_price = b2b_client_item_rate if b2b_client_item_rate else item.sales_price

            serialized_item = {
                'item_id': item.item_id,
                'item_no': item.item_no,
                'item_name': item.item_name,
                'item_type_name': item.type_id.type_name if hasattr(item, 'type_id') and item.type_id else "Unknown",
                'item_uom': item.item_uom_id.item_uom_name if hasattr(item, 'item_uom_id') and item.item_uom_id else "Unknown",
                'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else "Unknown",
                'store_id': stock_details.store_id.store_id if stock_details else "Unknown",
                'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
                'item_price': sales_price,
                'stock_qty': available_qty,
            }

            serialized_data.append(serialized_item)

        sorted_serialized_data = sorted(serialized_data, key=lambda x: x['stock_qty'], reverse=True)

        response_data = {
            'data': sorted_serialized_data,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'total_items': paginator.count,
        }

        cache.set(cache_key, response_data, 300)  # Cache response for 5 minutes

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# @login_required()
# def get_item_listAPI(request):
#     selected_store_id = request.GET.get('store_id')
#     selected_supplier_id = request.GET.get('filter_suppliers')
#     filter_org = request.GET.get('org_id')
#     b2b_client_supp = request.GET.get('b2b_client_supp_id')

#     serialized_data = []

#     try:
#         stock_data = stock_lists.objects.filter(is_approved=True, store_id=selected_store_id).values('item_id').annotate(total_stock_qty=Sum('stock_qty'))

#         for item in stock_data:
#             item_id = item['item_id']

#             item_query = items.objects.filter(item_id=item_id, org_id=filter_org)

#             if selected_supplier_id and selected_supplier_id != '1':
#                 item_query = item_query.filter(item_supplierdtl__supplier_id=selected_supplier_id)

#             item_details = item_query.first()

#             if item_details:
#                 supplier_data = item_supplierdtl.objects.filter(item_id=item_id).first()
#                 b2b_client_item_rate = None
                
#                 if b2b_client_supp:
#                     b2b_client_item_rate = b2b_client_item_rates.objects.filter(org_id=filter_org, supplier_id=b2b_client_supp, item_id=item_id).first()

#                 available_qty = get_available_qty(item_id, selected_store_id, filter_org)

#                 stock_details = stock_lists.objects.filter(item_id=item_id, store_id=selected_store_id).first()

#                 if b2b_client_item_rate:
#                     sales_price = b2b_client_item_rate.b2b_client_rate
#                 else:
#                     sales_price = item_details.sales_price

#                 serialized_item = {
#                     'item_id': item_id,
#                     'item_no': item_details.item_no,
#                     'item_name': item_details.item_name,
#                     'item_type_name': item_details.type_id.type_name,
#                     'item_uom': item_details.item_uom_id.item_uom_name,
#                     'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else "Unknown",
#                     'store_id': stock_details.store_id.store_id if stock_details else "Unknown",
#                     'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
#                     'item_price': sales_price,
#                     'stock_qty': available_qty,
#                 }

#                 serialized_data.append(serialized_item)

#         sorted_serialized_data = sorted(serialized_data, key=lambda x: x['stock_qty'], reverse=True)

#         return JsonResponse({'data': sorted_serialized_data})
    
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
    
# @login_required()
# def get_item_listAPI(request):
#     selected_store_id = request.GET.get('store_id')
#     selected_supplier_id = request.GET.get('filter_suppliers')
#     filter_org = request.GET.get('org_id')
#     b2b_client_supp = request.GET.get('b2b_client_supp_id')

#     try:
#         # Get the stock data with total quantity
#         stock_data = stock_lists.objects.filter(
#             is_approved=True, 
#             store_id=selected_store_id
#         ).values('item_id').annotate(total_stock_qty=Sum('stock_qty'))

#         # Get item ids
#         item_ids = [item['item_id'] for item in stock_data]

#         if not item_ids:
#             return JsonResponse({'data': []})

#         # Fetch items with related data
#         items_query = items.objects.filter(
#             item_id__in=item_ids,
#             org_id=filter_org
#         ).select_related('item_uom_id', 'type_id').prefetch_related(
#             Prefetch('item_supplierdtl_set', queryset=item_supplierdtl.objects.select_related('supplier_id'), to_attr='suppliers_detail')
#         )

#         if selected_supplier_id and selected_supplier_id != '1':
#             items_query = items_query.filter(item_supplierdtl__supplier_id=selected_supplier_id)

#         # Fetch b2b client rates if applicable
#         b2b_client_item_rates_map = {}
#         if b2b_client_supp:
#             b2b_client_item_rates_data = b2b_client_item_rates.objects.filter(
#                 org_id=filter_org, 
#                 supplier_id=b2b_client_supp, 
#                 item_id__in=item_ids
#             ).only('item_id', 'b2b_client_rate')
#             b2b_client_item_rates_map = {
#                 rate.item_id: rate.b2b_client_rate for rate in b2b_client_item_rates_data
#             }

#         # Fetch stock details
#         stock_details_map = {
#             stock.item_id: stock for stock in stock_lists.objects.filter(
#                 item_id__in=item_ids, 
#                 store_id=selected_store_id
#             ).select_related('store_id')
#         }

#         # Build response data
#         serialized_data = []
#         for item in items_query:
#             item_id = item.item_id
#             supplier_data = item.suppliers_detail[0] if item.suppliers_detail else None
#             b2b_client_item_rate = b2b_client_item_rates_map.get(item_id)
#             available_qty = get_available_qty(item_id, selected_store_id, filter_org)
#             # next((stock['total_stock_qty'] for stock in stock_data if stock['item_id'] == item_id), 0)

#             sales_price = b2b_client_item_rate or item.sales_price

#             stock_details = stock_details_map.get(item_id)

#             serialized_item = {
#                 'item_id': item_id,
#                 'item_no': item.item_no,
#                 'item_name': item.item_name,
#                 'item_type_name': item.type_id.type_name,
#                 'item_uom': item.item_uom_id.item_uom_name,
#                 'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else "Unknown",
#                 'store_id': stock_details.store_id.store_id if stock_details else "Unknown",
#                 'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
#                 'item_price': sales_price,
#                 'stock_qty': available_qty,
#             }

#             serialized_data.append(serialized_item)

#         # Sort data by stock quantity in descending order
#         sorted_serialized_data = sorted(serialized_data, key=lambda x: x['stock_qty'], reverse=True)

#         return JsonResponse({'data': sorted_serialized_data})

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


@login_required()
def select_item_listAPI(request):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        store_id = request.GET.get('store_id')
        selected_stock_id = request.GET.get('selectedItem')
        filter_org = request.GET.get('org_id')
        b2b_client_supp = request.GET.get('b2b_client_supp_id')

        try:
            get_itemID = items.objects.get(item_id=selected_stock_id, org_id=filter_org)
            stock_data = stock_lists.objects.filter(is_approved=True, item_id=get_itemID, store_id=store_id).values('item_id').annotate(total_stock_qty=Sum('stock_qty'))
            
            for item in stock_data:
                item_id = item['item_id']

                available_qty = get_available_qty(item_id, store_id, filter_org)
                
                item_id = get_itemID.item_id
                item_type_name = get_itemID.type_id.type_name

                supplier_data = item_supplierdtl.objects.filter(item_id=item_id).first()

                b2b_client_item_rate = None
            
                if b2b_client_supp:
                    b2b_client_item_rate = b2b_client_item_rates.objects.filter(org_id=filter_org, supplier_id=b2b_client_supp, item_id=item_id).first()

                stock_details = stock_lists.objects.filter(item_id=item_id, store_id=store_id).first()
                store = stock_details.store_id
                item_Supplier = supplier_data.supplier_id.supplier_name if supplier_data else None
                store_info = {
                    'store_id': store.store_id,
                    'store_name': store.store_name
                }

                if b2b_client_item_rate:
                    sales_price = b2b_client_item_rate.b2b_client_rate
                else:
                    sales_price = get_itemID.sales_price

                item_info = {
                    'store_id': store_info['store_id'],
                    'store_name': store_info['store_name'],
                    'item_id': item_id,
                    'item_name': get_itemID.item_name,
                    'item_no': get_itemID.item_no,
                    'item_type_name': item_type_name,
                    'extended_stock': get_itemID.extended_stock,
                    'stock_qty': available_qty,
                    'item_price': sales_price,
                    'item_uom': get_itemID.item_uom_id.item_uom_name,
                    'item_Supplier': item_Supplier,
                }

                return JsonResponse({'data': [item_info]})
            else:
                return JsonResponse({'data': []})
        except stock_lists.DoesNotExist:
            return JsonResponse({'error': 'Stock ID does not exist'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    

@login_required()
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    cash_point=data.get('cash_point')
    org_id = data.get('org')
    branch_id = data.get('branchs')
    supplier_id = data.get('supplier_id')
    driver_id = data.get('drivers_name')

    general_bill = data.get('general_bill', False)
    b2b_clients = data.get('b2b_clients', False)
    non_register = data.get('non_register', False)
    register = data.get('register', False)
    # cash_type = data.get('is_cash', False)
    # credit_type = data.get('is_credit', False)
    seller = data.get('seller', False)
    buyer = data.get('buyer', False)

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            cash_point_instance = store.objects.get(store_id=cash_point)

            if supplier_id:
                suppliers_instance = suppliers.objects.get(supplier_id=supplier_id)
            else:
                suppliers_instance = None
            
            if driver_id:
                drivers_instance = drivers_list.objects.get(driver_id=driver_id)
            else:
                drivers_instance = None

            invoice = invoice_list.objects.create(
                org_id=organization_instance,
                branch_id=branch_instance,
                supplier_id=suppliers_instance,
                driver_id=drivers_instance,
                cash_point=cash_point_instance,
                is_general_bill=general_bill,
                is_b2b_clients=b2b_clients,
                is_non_register=non_register,
                is_register=register,
                customer_name=data['customer_name'],
                gender = data.get('gender', ''),
                mobile_number=data['mobile_number'],
                house_no=data['house_no'],
                road_no=data['road_no'],
                sector_no=data['sector_no'],
                area=data['area'],
                address=data['address'],
                referral_person=data['referral_person'],
                ss_creator=request.user,
                ss_modifier=request.user
            )

            invoice_id = invoice.inv_id

            # Fetch all POST data at once
            item_data = list(zip(
                request.POST.getlist('item_id[]'),
                request.POST.getlist('store_id[]'),
                # request.POST.getlist('stock_id[]'),
                request.POST.getlist('sales_qty[]'),
                request.POST.getlist('item_price[]'),
                request.POST.getlist('item_w_dis[]'),
                request.POST.getlist('gross_dis[]'),
                request.POST.getlist('gross_vat_tax[]'),
            ))

            for item_id, store_id, qty, price, w_dis, dis, vat_tax in item_data:
                item_instance = items.objects.get(item_id=item_id)
                store_instance = store.objects.get(store_id=store_id)
                # stock_instance = stock_lists.objects.get(stock_id=stock_id)

                invoicedtl_list.objects.create(
                    inv_id=invoice,
                    item_id=item_instance,
                    store_id=store_instance,
                    # stock_id=stock_instance,
                    qty=qty,
                    sales_rate=price,
                    item_w_dis=w_dis,
                    gross_dis=dis,
                    gross_vat_tax=vat_tax,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

            given_amt = data['given_amt'] if data['given_amt'].strip() else 0
            change_amt = data['change_amt'] if data['change_amt'].strip() else 0

            pay_amt=data['receivable_amt']

            if int(pay_amt) > 0:
                payment = payment_list.objects.create(
                    inv_id=invoice,
                    pay_mode=data['pay_mode'],
                    collection_mode=data['Collection_mode'],
                    pay_amt=pay_amt,
                    given_amt=given_amt,
                    change_amt=change_amt,
                    card_info=data['card_info'],
                    pay_mob_number=data['pay_mob_number'],
                    pay_reference=data['pay_reference'],
                    bank_name=data['bank_name'],
                    remarks=data['remarks'],
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

            other_exps_amt=data['rent_other_expense']

            if int(other_exps_amt) > 0:
                other_exps_pay = rent_others_exps.objects.create(
                    inv_id=invoice,
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    is_seller=seller,
                    is_buyer=buyer,
                    other_exps_reason='Carrying Cost',
                    other_exps_amt=other_exps_amt,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

            resp['status'] = 'success'
            resp['invoice_id'] = invoice_id
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)


@login_required()
def searchb2bClientsInBillingAPI(request):
    data = []

    org_id_wise_filter = request.GET.get('org_filter', '')

    # Initialize an empty Q object for dynamic filters
    filter_kwargs = Q()

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Include the static flags in the filter
    static_filters = Q(b2bclient_flag=4)

    # Combine static filters with dynamic filters
    combined_filters = static_filters & filter_kwargs

    # Apply combined_filters to the query
    supp_data = suppliers.objects.filter(is_active=True).filter(combined_filters)

    for supp_item in supp_data:
        data.append({
            'supplier_id': supp_item.supplier_id,
            'supplier_name': supp_item.supplier_name,
        })

    return JsonResponse({'data': data})


@login_required()
def selectB2bClientsDetailsAPI(request):
    if request.method == 'GET' and 'selectedb2bClient' in request.GET:
        selected_b2b_client = request.GET.get('selectedb2bClient')

        try:
            selected_b2bClient = suppliers.objects.get(supplier_id=selected_b2b_client)

            b2bClient_details = []

            b2bClient_details.append({
                'supplier_id': selected_b2bClient.supplier_id,
                'supplier_no': selected_b2bClient.supplier_no,
                'supplier_name': selected_b2bClient.supplier_name,
                'phone': selected_b2bClient.phone if selected_b2bClient.phone else '',
                'address': selected_b2bClient.address if selected_b2bClient.address else '',
            })

            return JsonResponse({'data': b2bClient_details})
        except suppliers.DoesNotExist:
            return JsonResponse({'error': 'suppliers not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required()
def receipt(request):
    id = request.GET.get('id')

    sales = invoice_list.objects.filter(inv_id=id).first()
    transaction = {}
    for field in invoice_list._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)
        if 'customer_name' in transaction:
            transaction['customer_name'] = transaction['customer_name']

    ItemList = invoicedtl_list.objects.filter(inv_id=sales).all()
    PayList = payment_list.objects.filter(inv_id=sales).all()
    carrying_cost_buyer = rent_others_exps.objects.filter(inv_id=sales, is_buyer=True).all()
    carrying_cost_seller = rent_others_exps.objects.filter(inv_id=sales, is_seller=True).all()

    # Gross Total Amt. = qty * sales_rate - item_w_dis_sum = grand total
    grand_total = 0  # Initialize the grand_total
    grand_gross_dis = 0
    grand_gross_vat_tax = 0
    total_collection_amt = 0
    

    # Initialize the variables
    collection_amt_sum = 0
    due_collection_amt_sum = 0
    refund_amt_sum = 0
    adjust_amt_sum = 0
    total_net_collection = 0
    total_cost_buyer_amt = 0
    total_cost_seller_amt = 0

    for item in ItemList:
        # Calculate the total bill for each item
        item.total_bill = (item.qty - item.is_cancel_qty) * item.sales_rate

        # individual discount
        item.item_wise_disc = (item.item_w_dis / item.qty) * (item.qty - item.is_cancel_qty)
        # total qty = qty - cancel qty
        item.qty_cancelQty = item.qty - item.is_cancel_qty
        # cancel item_w_dis amount
        item.item_w_dis_cancel_amt = (item.item_w_dis / item.qty) * item.is_cancel_qty

        # individual item total
        item.total_amount = (item.sales_rate * (item.qty - item.is_cancel_qty)) - (item.item_w_dis - item.item_w_dis_cancel_amt)
        grand_total += item.total_amount  # Add the item's total bill to the grand_total
        # print('total_amount', item.total_amount)

        # gross discount
        item.gross_dis_inv_amt = (item.gross_dis / item.qty) * item.is_cancel_qty
        item.total_gross_dis_with_calcel = item.gross_dis - item.gross_dis_inv_amt
        grand_gross_dis += item.total_gross_dis_with_calcel
        grand_gross_dis = round(grand_gross_dis, 3)

        # gross vat tax
        item.gross_vat_tax_inv_amt = (item.gross_vat_tax / item.qty) * item.is_cancel_qty
        item.total_gross_vat_tax_with_calcel = item.gross_vat_tax - item.gross_vat_tax_inv_amt
        grand_gross_vat_tax += item.total_gross_vat_tax_with_calcel
        grand_gross_vat_tax = round(grand_gross_vat_tax, 3)
    
    # carrying cost from buyer
    for cost_buyer in carrying_cost_buyer:
        cost_buyer_amt = cost_buyer.other_exps_amt
        total_cost_buyer_amt += cost_buyer_amt

    # carrying cost from seller
    for cost_seller in carrying_cost_seller:
        cost_seller_amt = cost_seller.other_exps_amt
        total_cost_seller_amt += cost_seller_amt


    # grand_total + grand_gross_vat_tax - grand_gross_dis
    net_total_amt = (grand_total + grand_gross_vat_tax + total_cost_buyer_amt) - grand_gross_dis
    net_total_amt = round(net_total_amt, 1)

    # pay amount value and find out due value
    # Filter PayList for collection_mode="1" and sum the payments
    collection_amt = PayList.filter(collection_mode="1")
    collection_amt_result = collection_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if collection_amt_result['pay_amt_sum'] is not None:
        collection_amt_sum = collection_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="2" and sum the payments
    due_collection_amt = PayList.filter(collection_mode="2")
    due_collection_amt_result = due_collection_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if due_collection_amt_result['pay_amt_sum'] is not None:
        due_collection_amt_sum = due_collection_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="3" and sum the payments
    refund_amt = PayList.filter(collection_mode="3")
    refund_amt_result = refund_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if refund_amt_result['pay_amt_sum'] is not None:
        refund_amt_sum = refund_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="4" and sum the payments
    adjust_amt = PayList.filter(collection_mode="4")
    adjust_amt_result = adjust_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if adjust_amt_result['pay_amt_sum'] is not None:
        adjust_amt_sum = adjust_amt_result['pay_amt_sum']

    # total payment = collection + due collection - refund
    total_collection_amt = collection_amt_sum + due_collection_amt_sum + adjust_amt_sum
    # total net collection
    total_net_collection = total_collection_amt - refund_amt_sum

    # net_due_amt = net_total_amt - pay_amt_sum
    net_due_amt = (net_total_amt - (total_collection_amt - refund_amt_sum))
    # Calculate the net_due_amt and round it to 2 decimal places
    net_due_amt = round(net_due_amt, 0)

    # inword query
    # Convert total_collection_amt to words
    words = num2words(total_collection_amt)

    context = {
        "transaction": transaction,
        "salesItems": ItemList,
        "PayList": PayList,
        'grand_total': grand_total,
        "grand_gross_dis": grand_gross_dis,
        'grand_gross_vat_tax': grand_gross_vat_tax,
        'net_total_amt': net_total_amt,
        'net_due_amt': net_due_amt,
        "numbers_as_words": words,
        "total_collection_amt": total_collection_amt,
        "refund_amt_sum": refund_amt_sum,
        "total_net_collection": total_net_collection,
        "total_cost_buyer_amt": total_cost_buyer_amt,
        "total_cost_seller_amt": total_cost_seller_amt,
    }
    
    return render(request, 'item_pos/receipt.html', context)


@login_required()
def deliveryChalan(request):
    id = request.GET.get('id')

    sales = invoice_list.objects.filter(inv_id=id).first()
    transaction = {}
    for field in invoice_list._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)
        if 'customer_name' in transaction:
            transaction['customer_name'] = transaction['customer_name']

    ItemList = invoicedtl_list.objects.filter(inv_id=sales).all()
    PayList = payment_list.objects.filter(inv_id=sales).all()

    # Gross Total Amt. = qty * sales_rate - item_w_dis_sum = grand total
    grand_total = 0  # Initialize the grand_total
    grand_gross_dis = 0
    grand_gross_vat_tax = 0
    total_collection_amt = 0
    grand_total_qty = 0

    # Initialize the variables
    collection_amt_sum = 0
    due_collection_amt_sum = 0
    refund_amt_sum = 0
    adjust_amt_sum = 0
    total_net_collection = 0

    for item in ItemList:
        # Calculate the total bill for each item
        item.total_bill = (item.qty - item.is_cancel_qty) * item.sales_rate

        # individual discount
        item.item_wise_disc = (item.item_w_dis / item.qty) * (item.qty - item.is_cancel_qty)
        # total qty = qty - cancel qty
        item.qty_cancelQty = item.qty - item.is_cancel_qty
        grand_total_qty += item.qty_cancelQty
        # cancel item_w_dis amount
        item.item_w_dis_cancel_amt = (item.item_w_dis / item.qty) * item.is_cancel_qty

        # individual item total
        item.total_amount = (item.sales_rate * (item.qty - item.is_cancel_qty)) - (item.item_w_dis - item.item_w_dis_cancel_amt)
        grand_total += item.total_amount  # Add the item's total bill to the grand_total
        # print('total_amount', item.total_amount)

        # gross discount
        item.gross_dis_inv_amt = (item.gross_dis / item.qty) * item.is_cancel_qty
        item.total_gross_dis_with_calcel = item.gross_dis - item.gross_dis_inv_amt
        grand_gross_dis += item.total_gross_dis_with_calcel
        grand_gross_dis = round(grand_gross_dis, 3)

        # gross vat tax
        item.gross_vat_tax_inv_amt = (item.gross_vat_tax / item.qty) * item.is_cancel_qty
        item.total_gross_vat_tax_with_calcel = item.gross_vat_tax - item.gross_vat_tax_inv_amt
        grand_gross_vat_tax += item.total_gross_vat_tax_with_calcel
        grand_gross_vat_tax = round(grand_gross_vat_tax, 3)

    # grand_total + grand_gross_vat_tax - grand_gross_dis
    net_total_amt = grand_total + grand_gross_vat_tax - grand_gross_dis
    net_total_amt = round(net_total_amt, 1)

    # pay amount value and find out due value
    # Filter PayList for collection_mode="1" and sum the payments
    collection_amt = PayList.filter(collection_mode="1")
    collection_amt_result = collection_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if collection_amt_result['pay_amt_sum'] is not None:
        collection_amt_sum = collection_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="2" and sum the payments
    due_collection_amt = PayList.filter(collection_mode="2")
    due_collection_amt_result = due_collection_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if due_collection_amt_result['pay_amt_sum'] is not None:
        due_collection_amt_sum = due_collection_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="3" and sum the payments
    refund_amt = PayList.filter(collection_mode="3")
    refund_amt_result = refund_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if refund_amt_result['pay_amt_sum'] is not None:
        refund_amt_sum = refund_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="4" and sum the payments
    adjust_amt = PayList.filter(collection_mode="4")
    adjust_amt_result = adjust_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if adjust_amt_result['pay_amt_sum'] is not None:
        adjust_amt_sum = adjust_amt_result['pay_amt_sum']

    # total payment = collection + due collection - refund
    total_collection_amt = collection_amt_sum + due_collection_amt_sum + adjust_amt_sum
    # total net collection
    total_net_collection = total_collection_amt - refund_amt_sum

    # net_due_amt = net_total_amt - pay_amt_sum
    net_due_amt = net_total_amt - (total_collection_amt - refund_amt_sum)
    # Calculate the net_due_amt and round it to 2 decimal places
    net_due_amt = round(net_due_amt, 0)

    # inword query
    # Convert net_total_amt to words
    words = num2words(net_total_amt)

    context = {
        "transaction": transaction,
        "salesItems": ItemList,
        "PayList": PayList,
        'grand_total': grand_total,
        'grand_total_qty': grand_total_qty,
        "grand_gross_dis": grand_gross_dis,
        'grand_gross_vat_tax': grand_gross_vat_tax,
        'net_total_amt': net_total_amt,
        'net_due_amt': net_due_amt,
        "numbers_as_words": words,
        "total_collection_amt": total_collection_amt,
        "refund_amt_sum": refund_amt_sum,
        "total_net_collection": total_net_collection,
        "sales": sales,
    }
    
    return render(request, 'item_pos/delivery_chalan.html', context)

# ========================================== Rent/Others Expense ==========================================

@login_required()
def rentOthersExpsManagerAPI(request):
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
    return render(request, 'rent_others_exps/rent_others_exps.html', context)

@login_required()
def getRentOthersExpsListsAPI(request):
    # Retrieve filter parameters from the frontend
    is_seller_wise_filter = request.GET.get('is_seller')
    is_buyer_wise_filter = request.GET.get('is_buyer')
    org_id_wise_filter = request.GET.get('org_id')
    branch_id_wise_filter = request.GET.get('branch_id')
    start_date_wise_filter = request.GET.get('start_date')
    end_date_wise_filter = request.GET.get('end_date')

    filter_kwargs = Q()

    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)
    
    if branch_id_wise_filter:  # Exclude branch_id if it's not provided
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)
        
    # Add date range filter conditions if start_date and end_date are provided
    if start_date_wise_filter and end_date_wise_filter:
        start_date = datetime.strptime(start_date_wise_filter, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_wise_filter, '%Y-%m-%d')
        filter_kwargs &= Q(other_exps_date__range=(start_date, end_date))

    if is_seller_wise_filter == 'true':
        filter_kwargs &= Q(is_seller=True)
    elif is_buyer_wise_filter == 'true':
        filter_kwargs &= Q(is_buyer=True)

    # Apply dynamic filters to rent_others_exps queryset
    expense_data = rent_others_exps.objects.filter(filter_kwargs)
    
    # Convert expense data to a list of dictionaries
    expenData = []
    for expense in expense_data:
        expenData.append({
            'other_exps_id': expense.other_exps_id,
            'inv_id': expense.inv_id.inv_id if expense.inv_id else None,
            'exps_reason': expense.other_exps_reason,
            'exps_date': expense.other_exps_date,
            'is_seller': expense.is_seller,
            'is_buyer': expense.is_buyer,
            'exps_amt': expense.other_exps_amt,
        })

    # Return the filtered data as JSON
    return JsonResponse({'expen_val': expenData})

# add Expenses modal
@login_required()
def addExpensesModelManageAPI(request):
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
    return render(request, 'rent_others_exps/add_others_exps.html', context)


# Expense add/update view
@login_required()
def addExpenseAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org_id')
    branch_id = data.get('branch_id')

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)

            driver_data = rent_others_exps()

            # Update or set the fields based on request data
            driver_data.other_exps_amt = data.get('expense_amt')
            driver_data.other_exps_reason = data.get('expense_reason')
            driver_data.org_id = organization_instance
            driver_data.branch_id = branch_instance
            driver_data.ss_creator = request.user
            driver_data.ss_modifier = request.user
            driver_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)

# @login_required()
# def get_item_listAPI(request):
#     selected_store_id = request.GET.get('store_id')
#     selected_supplier_id = request.GET.get('filter_suppliers')
    
#     stock_data = stock_lists.objects.filter(is_approved=True, store_id=selected_store_id).values('item_id').annotate(total_stock_qty=Sum('stock_qty'))

#     serialized_data = []

#     for item in stock_data:
#         item_id = item['item_id']
#         stock_total_qty = item['total_stock_qty']

#         # Get item details
#         item_query = items.objects.filter(item_id=item_id)
        
#         # Filter items based on supplier_id if provided and not default '1'
#         if selected_supplier_id and selected_supplier_id != '1':
#             item_query = item_query.filter(item_supplierdtl__supplier_id=selected_supplier_id)
        
#         item_details = item_query.first()
        
#         if item_details:
#             # Getting the first supplier data for the item, using the filtered item_query
#             supplier_data = item_supplierdtl.objects.filter(item_id=item_id).first()

#             # Aggregate sales data
#             invoice_details = invoicedtl_list.objects.filter(item_id=item_id, store_id=selected_store_id)
#             sales_total_qty = invoice_details.aggregate(
#                 sales_total_qty=Sum(ExpressionWrapper(
#                     F('qty') - F('is_cancel_qty'), output_field=FloatField())
#                 )
#             )['sales_total_qty'] or 0

#             available_qty = stock_total_qty - sales_total_qty

#             # if available_qty > 0:
#             stock_details = stock_lists.objects.filter(item_id=item_id, store_id=selected_store_id).first()

#             sales_price = item_details.sales_price
                
#             # Prepare serialized data with supplier information
#             serialized_item = {
#                 'item_id': item_id,
#                 'item_no': item_details.item_no,
#                 'item_name': item_details.item_name,
#                 'item_type_name': item_details.type_id.type_name,
#                 'item_uom': item_details.item_uom_id.item_uom_name,
#                 'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else "Unknown",
#                 'store_id': stock_details.store_id.store_id if stock_details else "Unknown",
#                 'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
#                 'item_price': sales_price,
#                 'stock_qty': available_qty,
#             }

#             serialized_data.append(serialized_item)

#     # Sort data by stock quantity in descending order
#     sorted_serialized_data = sorted(serialized_data, key=lambda x: x['stock_qty'], reverse=True)

#     return JsonResponse({'data': sorted_serialized_data})


# @login_required()
# def save_pos(request):
#     resp = {'status': 'failed', 'msg': ''}
#     data = request.POST

#     try:
#         with transaction.atomic():
#             # invoice table
#             invoice = invoice_list(
#                 customer_name=data['customer_name'],
#                 gender=data['gender'],
#                 mobile_number=data['mobile_number'],
#                 cash_point=data['cash_point'],
#                 referral_person=data['referral_person'],
#                 ss_creator=request.user,
#                 ss_modifier=request.user
#             ).save()

#             invoice_id = invoice_list.objects.last().pk
#             invoice = invoice_list.objects.filter(inv_id=invoice_id).first()

#             # Invoice details list
#             # get datalist from form
#             item_ids = request.POST.getlist('item_id[]')
#             store_ids = request.POST.getlist('store_id[]')
#             stock_ids = request.POST.getlist('stock_id[]')
#             sales_qtys = request.POST.getlist('sales_qty[]')
#             item_prices = request.POST.getlist('item_price[]')
#             item_w_disc = request.POST.getlist('item_w_dis[]')
#             gross_disc = request.POST.getlist('gross_dis[]')
#             gross_vat_taxs = request.POST.getlist('gross_vat_tax[]')

#             # Invoice details list print
#             print({
#                 'invoice_id': invoice,
#                 'item_id': item_ids,
#                 'store_id': store_ids,
#                 'stock_id': stock_ids,
#                 'sales_qty': sales_qtys,
#                 'item_price': item_prices,
#                 'item_w_dis': item_w_disc,
#                 'item_w_dis': gross_disc,
#                 'gross_vat_tax': gross_vat_taxs
#             })

#             for item_id, store_id, stock_id, qty, price, w_dis, dis, vat_tax in zip(item_ids, store_ids, stock_ids, sales_qtys, item_prices, item_w_disc, gross_disc, gross_vat_taxs):

#                 item_instance = items.objects.get(item_id=item_id)
#                 store_instance = store.objects.get(store_id=store_id)
#                 stock_instance = stock_lists.objects.get(stock_id=stock_id)

#                 invoice_detail = invoicedtl_list(
#                     inv_id=invoice,
#                     item_id=item_instance,
#                     store_id=store_instance,
#                     stock_id=stock_instance,
#                     qty=qty,
#                     sales_rate=price,
#                     item_w_dis=w_dis,
#                     gross_dis=dis,
#                     gross_vat_tax=vat_tax,
#                     ss_creator=request.user,
#                     ss_modifier=request.user,
#                 )
#                 invoice_detail.save()

#             # payment table
#             payment = payment_list(
#                 inv_id=invoice,
#                 pay_mode=data['pay_mode'],
#                 collection_mode=data['Collection_mode'],
#                 pay_amt=data['receivable_amt'],
#                 given_amt=data['given_amt'],
#                 change_amt=data['change_amt'],
#                 card_info=data['card_info'],
#                 pay_mob_number=data['pay_mob_number'],
#                 pay_reference=data['pay_reference'],
#                 bank_name=data['bank_name'],
#                 remarks=data['remarks'],
#                 ss_creator=request.user,
#                 ss_modifier=request.user,
#             )
#             payment.save()

#             resp['status'] = 'success'
#             resp['invoice_id'] = invoice_id
#             # messages.success(request, "Sales Successful!...")
#     except:
#         print("Unexpected error:", sys.exc_info()[0])
#     # return redirect('pos_billing')
#     return HttpResponse(json.dumps(resp), content_type="application/json")