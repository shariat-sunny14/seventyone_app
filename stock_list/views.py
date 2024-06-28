import json
from django.forms import ValidationError
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count, IntegerField, Value, Prefetch
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.views.decorators.http import require_POST
from collections import defaultdict
from django.db.models import FloatField
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from item_pos.models import invoicedtl_list
from store_setup.models import store
from item_setup.models import items, item_supplierdtl
from po_return.models import po_return_details
from organizations.models import organizationlst
from supplier_setup.models import suppliers
from . models import stock_lists
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def stockListManagerAPI(request):
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
        
    store_data = store.objects.filter(is_main_store=True).all().order_by('store_name')
    stock_batch = stock_lists.objects.filter(is_approved=True).values('item_batch').annotate(count=Count('item_batch')).order_by('item_batch')

    context = {
        'store_data': store_data,
        'stock_batch': stock_batch,
        'org_list': org_list,
    }

    return render(request, 'stock_list/stock_list.html', context)

# Item wise stock list
@login_required
def getItemWiseStockAPI(request):
    selected_store_id = request.GET.get('store_id')

    cache_key = f"store_{selected_store_id}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return JsonResponse(cached_response)

    item_details = items.objects.filter(is_active=True)

    item_ids = list(item_details.values_list('item_id', flat=True))

    stock_data = stock_lists.objects.filter(
        is_approved=True,
        store_id=selected_store_id,
        item_id__in=item_ids
    ).values('item_id').annotate(
        total_stock_qty=Sum('stock_qty', output_field=FloatField())
    )

    stock_qty_dict = {stock['item_id']: stock['total_stock_qty'] for stock in stock_data}

    sales_data = invoicedtl_list.objects.filter(
        item_id__in=item_ids, store_id=selected_store_id
    ).values('item_id').annotate(
        sales_total_qty=Sum(F('qty') - F('is_cancel_qty'), output_field=FloatField())
    )

    sales_qty_dict = {sale['item_id']: sale['sales_total_qty'] for sale in sales_data}

    return_data = po_return_details.objects.filter(
        item_id__in=item_ids, store_id=selected_store_id
    ).values('item_id').annotate(
        tot_return_qty=Sum('return_qty', output_field=FloatField())
    )

    return_qty_dict = {ret['item_id']: ret['tot_return_qty'] for ret in return_data}

    serialized_data = []
    for item in item_details.prefetch_related(
        'item_supplierdtl_set',  # Prefetch related item_supplierdtl_set
        'item_supplierdtl_set__supplier_id',  # Prefetch supplier_id within item_supplierdtl_set
        'item_supplierdtl_set__ss_creator',  # Prefetch ss_creator within item_supplierdtl_set
        'item_supplierdtl_set__ss_modifier',  # Prefetch ss_modifier within item_supplierdtl_set
    ).select_related(
        'type_id', 'item_uom_id', 'supplier_id',  # Select related fields on items model
    ):
        total_stock_qty = stock_qty_dict.get(item.item_id, 0)
        if total_stock_qty == 0:
            continue

        sales_total_qty = sales_qty_dict.get(item.item_id, 0)
        tot_return_qty = return_qty_dict.get(item.item_id, 0)
        total_stockQty = total_stock_qty - (sales_total_qty + tot_return_qty)

        supplier_instance = None
        if item.item_supplierdtl_set.exists():
            supplier_instance = item.item_supplierdtl_set.first().supplier_id.supplier_name

        serialized_item = {
            'item_no': item.item_no,
            'item_name': item.item_name,
            'item_type_name': item.type_id.type_name if item.type_id else "Unknown",
            'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else "Unknown",
            'item_Supplier': supplier_instance,
            'item_p_price': item.purchase_price if item.purchase_price else "N/A",
            'item_s_price': item.sales_price if item.sales_price else "N/A",
            'total_stockQty': total_stockQty,
        }

        serialized_data.append(serialized_item)

    response_data = {
        'data': serialized_data,
        'total_items': len(serialized_data),
    }

    cache.set(cache_key, response_data, timeout=60*5)  # Cache the response for 5 minutes
    return JsonResponse(response_data)


@login_required
def stockReportManagerAPI(request, store_id=None):
    org_id = request.GET.get('org_id')
    selected_store_id = store_id  # Using store_id directly from the URL

    org_data = organizationlst.objects.filter(is_active=True, org_id=org_id).values('org_name', 'address', 'email', 'website', 'phone', 'hotline', 'fax').first()

    # Fetch active items
    item_details = items.objects.filter(is_active=True)

    # Extract item IDs
    item_ids = list(item_details.values_list('item_id', flat=True))

    store_name = store.objects.filter(is_active=True, store_id=selected_store_id).values('store_name').first()

    # Fetch stock data
    stock_data = stock_lists.objects.filter(
        is_approved=True,
        store_id=selected_store_id,
        item_id__in=item_ids
    ).values('item_id').annotate(
        total_stock_qty=Sum('stock_qty', output_field=FloatField())
    )

    # Create stock quantity dictionary
    stock_qty_dict = {stock['item_id']: stock['total_stock_qty'] for stock in stock_data}

    # Fetch sales data
    sales_data = invoicedtl_list.objects.filter(
        item_id__in=item_ids, store_id=selected_store_id
    ).values('item_id').annotate(
        sales_total_qty=Sum(F('qty') - F('is_cancel_qty'), output_field=FloatField())
    )

    # Create sales quantity dictionary
    sales_qty_dict = {sale['item_id']: sale['sales_total_qty'] for sale in sales_data}

    # Fetch return data
    return_data = po_return_details.objects.filter(
        item_id__in=item_ids, store_id=selected_store_id
    ).values('item_id').annotate(
        tot_return_qty=Sum('return_qty', output_field=FloatField())
    )

    # Create return quantity dictionary
    return_qty_dict = {ret['item_id']: ret['tot_return_qty'] for ret in return_data}

    # Serialize item details
    serialized_items = []

    for item in item_details.prefetch_related(
        'item_supplierdtl_set__supplier_id',
        'item_supplierdtl_set__ss_creator',
        'item_supplierdtl_set__ss_modifier'
    ).select_related(
        'type_id', 'item_uom_id', 'supplier_id'
    ):
        total_stock_qty = stock_qty_dict.get(item.item_id, 0)
        if total_stock_qty == 0:
            continue

        sales_total_qty = sales_qty_dict.get(item.item_id, 0)
        tot_return_qty = return_qty_dict.get(item.item_id, 0)
        total_stockQty = total_stock_qty - (sales_total_qty + tot_return_qty)

        supplier_instance = None
        if item.item_supplierdtl_set.exists():
            supplier_instance = item.item_supplierdtl_set.first().supplier_id.supplier_name

        serialized_item = {
            'item_no': item.item_no,
            'item_name': item.item_name,
            'item_type_name': item.type_id.type_name if item.type_id else "Unknown",
            'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else "Unknown",
            'item_Supplier': supplier_instance,
            'item_p_price': item.purchase_price if item.purchase_price else "N/A",
            'item_s_price': item.sales_price if item.sales_price else "N/A",
            'total_stockQty': total_stockQty,
        }
        serialized_items.append(serialized_item)

    context = {
        'data': serialized_items,
        'org_name': org_data['org_name'],
        'address': org_data['address'],
        'email': org_data['email'],
        'website': org_data['website'],
        'phone': org_data['phone'],
        'hotline': org_data['hotline'],
        'fax': org_data['fax'],
        'store_name': store_name['store_name'] if store_name else "Unknown",
    }

    return render(request, 'stock_list/stock_report.html', context)


# @login_required
# def getItemWiseStockAPI(request):
#     selected_store_id = request.GET.get('store_id')
#     search_query = request.GET.get('search_item')

#     # Fetch and annotate stock data in a single query
#     stock_data = (
#         stock_lists.objects.filter(is_approved=True, store_id=selected_store_id)
#         .values('item_id', 'store_id')
#         .annotate(total_stock_qty=Sum('stock_qty'))
#     )

#     item_ids = [item['item_id'] for item in stock_data]

#     # Use prefetch_related to fetch related data in fewer queries
#     items_data = (
#         items.objects.filter(item_id__in=item_ids)
#         .select_related('type_id', 'item_uom_id', 'supplier_id')
#         .prefetch_related('item_supplierdtl_set')
#     )

#     invoice_details_data = invoicedtl_list.objects.filter(item_id__in=item_ids, store_id=selected_store_id)
#     po_return_details_data = po_return_details.objects.filter(item_id__in=item_ids, store_id=selected_store_id)

#     # Aggregate sales and return quantities in fewer queries
#     sales_aggregates = invoice_details_data.values('item_id').annotate(
#         sales_total_qty=Sum(ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField()))
#     )
#     returns_aggregates = po_return_details_data.values('item_id').annotate(
#         tot_return_qty=Sum('return_qty')
#     )

#     # Convert aggregates to dictionaries for faster lookup
#     sales_aggregates_dict = {item['item_id']: item['sales_total_qty'] for item in sales_aggregates}
#     returns_aggregates_dict = {item['item_id']: item['tot_return_qty'] for item in returns_aggregates}

#     serialized_data = []

#     for stock in stock_data:
#         item_id = stock['item_id']
#         stock_total_qty = stock['total_stock_qty']

#         item_details = next((item for item in items_data if item.item_id == item_id), None)
#         if not item_details or (search_query and search_query.lower() not in item_details.item_name.lower()):
#             continue

#         sales_total_qty = sales_aggregates_dict.get(item_id, 0)
#         tot_return_qty = returns_aggregates_dict.get(item_id, 0)
#         total_stockQty = stock_total_qty - (sales_total_qty + tot_return_qty)

#         supplier_instance = item_details.item_supplierdtl_set.first().supplier_id if item_details.item_supplierdtl_set.exists() else None
#         store_name = store.objects.get(store_id=selected_store_id).store_name

#         serialized_item = {
#             'item_no': item_details.item_no,
#             'item_name': item_details.item_name,
#             'item_type': item_details.type_id.type_name if item_details.type_id else None,
#             'item_uom': item_details.item_uom_id.item_uom_name if item_details.item_uom_id else None,
#             'item_Supplier': supplier_instance.supplier_name if supplier_instance else None,
#             'item_Manufacturer': item_details.supplier_id.supplier_name if item_details.supplier_id else None,
#             'store_name': store_name,
#             'item_p_price': item_details.purchase_price,
#             'item_s_price': item_details.sales_price,
#             'total_stockQty': total_stockQty,
#         }

#         serialized_data.append(serialized_item)

#     sorted_serialized_data = sorted(serialized_data, key=lambda x: x['total_stockQty'], reverse=True)

#     return JsonResponse({'data': sorted_serialized_data})