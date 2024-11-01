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
from . models import in_stock, stock_lists
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
    
    context = {
        'org_list': org_list,
    }

    return render(request, 'stock_list/stock_list.html', context)

# Item wise stock list
@login_required
def getItemWiseStockAPI(request):
    selected_store_id = request.GET.get('store_id')

    try:
        # Fetch active items from the items table
        item_details = items.objects.filter(is_active=True)

        # Get a list of item IDs from the active items
        item_ids = list(item_details.values_list('item_id', flat=True))

        if selected_store_id == '1':
            # Sum stock_qty for each item across all stores
            stock_data = in_stock.objects.filter(item_id__in=item_ids).values('item_id').annotate(total_stock_qty=Sum('stock_qty'))
        else:
            # Fetch stock for the specified store without aggregation
            stock_data = in_stock.objects.filter(
                store_id=selected_store_id,
                item_id__in=item_ids
            ).values('item_id', 'stock_qty')

        # Create a dictionary for stock quantities
        stock_data_dict = {}
        for stock in stock_data:
            # If 'total_stock_qty' exists (for store_id == '1'), use it, otherwise use 'stock_qty'
            if 'total_stock_qty' in stock:
                stock_data_dict[stock['item_id']] = stock['total_stock_qty']
            else:
                stock_data_dict[stock['item_id']] = stock['stock_qty']

        # Filter item_details to include only items that have a corresponding stock entry
        item_details = item_details.filter(item_id__in=stock_data_dict.keys())

        serialized_data = []
        for item in item_details.prefetch_related(
            'item_supplierdtl_set',  # Prefetch related item_supplierdtl_set
            'item_supplierdtl_set__supplier_id',  # Prefetch supplier_id within item_supplierdtl_set
        ).select_related(
            'type_id', 'item_uom_id', 'supplier_id',  # Select related fields on items model
        ):
            # Get the total stock quantity from the stock_data_dict
            total_stock_qty = stock_data_dict.get(item.item_id, 0)

            # Get the supplier instance if available
            supplier_instance = None
            if item.item_supplierdtl_set.exists():
                supplier_instance = item.item_supplierdtl_set.first().supplier_id.supplier_name

            # Prepare the serialized item data
            serialized_item = {
                'item_no': item.item_no,
                'item_name': item.item_name,
                'item_type_name': item.type_id.type_name if item.type_id else "Unknown",
                'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else "Unknown",
                'item_Supplier': supplier_instance,
                'item_p_price': item.purchase_price if item.purchase_price else "N/A",
                'item_s_price': item.sales_price if item.sales_price else "N/A",
                'total_stockQty': total_stock_qty,
            }

            serialized_data.append(serialized_item)

        # Prepare the response data
        response_data = {
            'data': serialized_data,
            'total_items': len(serialized_data),
        }

        # Return the response as JSON
        return JsonResponse(response_data)

    except Exception as e:
        # Handle any potential errors
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def stockReportManagerAPI(request, store_id=None):
    org_id = request.GET.get('org_id')
    selected_store_id = store_id  # Using store_id directly from the URL

    # Fetch organization data
    org_data = organizationlst.objects.filter(is_active=True, org_id=org_id).values(
        'org_name', 'address', 'email', 'website', 'phone', 'hotline', 'fax'
    ).first()

    # Fetch all active items
    item_details = items.objects.filter(is_active=True)

    item_ids = list(item_details.values_list('item_id', flat=True))

    # Fetch stock data based on selected store
    if selected_store_id == 1:
        # Sum stock_qty for each item across all stores
        stock_data = in_stock.objects.filter(item_id__in=item_ids).values('item_id').annotate(total_stock_qty=Sum('stock_qty'))
    else:
        # Fetch stock for the specified store without aggregation
        stock_data = in_stock.objects.filter(
            store_id=selected_store_id,
            item_id__in=item_ids
        ).values('item_id', 'stock_qty')

    # Check if stock data is empty
    if not stock_data:
        print("No stock data found for the selected store.")
    
    # Create a dictionary for stock quantities
    stock_data_dict = {stock['item_id']: stock.get('total_stock_qty', stock.get('stock_qty', 0)) for stock in stock_data}

    # Filter item_details to include only items that have a corresponding stock entry
    item_details = item_details.filter(item_id__in=stock_data_dict.keys())

    # Fetch store name
    store_name = store.objects.filter(is_active=True, store_id=selected_store_id).values('store_name').first()

    serialized_items = []

    for item in item_details.prefetch_related(
        'item_supplierdtl_set',
        'item_supplierdtl_set__supplier_id',
    ).select_related(
        'type_id', 'item_uom_id', 'supplier_id',
    ):
        total_stock_qty = stock_data_dict.get(item.item_id, 0)

        supplier_instance = item.item_supplierdtl_set.first().supplier_id.supplier_name if item.item_supplierdtl_set.exists() else None

        serialized_item = {
            'item_no': item.item_no,
            'item_name': item.item_name,
            'item_type_name': item.type_id.type_name if item.type_id else "Unknown",
            'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else "Unknown",
            'item_Supplier': supplier_instance,
            'item_p_price': item.purchase_price or "N/A",
            'item_s_price': item.sales_price or "N/A",
            'total_stockQty': total_stock_qty,
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
        'store_name': store_name['store_name'] if store_name else "All Store",
    }

    return render(request, 'stock_list/stock_report.html', context)