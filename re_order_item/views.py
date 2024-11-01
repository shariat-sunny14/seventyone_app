import sys
import json
from datetime import datetime
from django.db.models import Q, F, Sum, FloatField, ExpressionWrapper
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from item_pos.models import invoice_list, invoicedtl_list, payment_list
from store_setup.models import store
from item_setup.models import item_supplierdtl, items
from stock_list.models import in_stock, stock_lists
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def reOrderItemListAPI(request):
    store_data = store.objects.filter(is_main_store=True).all().order_by('store_name')

    context = {
        'store_data': store_data,
    }

    return render(request, 're_order_item/re_order_item.html', context)


@login_required()
def getReOrderItemsAPI(request):
    selected_store_id = request.GET.get('store_id')
    search_query = request.GET.get('search_item')

    # Check if "All Store" is selected
    stock_data = in_stock.objects.filter(store_id=selected_store_id).values('item_id', 'stock_qty')

    serialized_data = []

    for item in stock_data:
        item_id = item['item_id']
        stock_qty = item['stock_qty']

        supplier_data = item_supplierdtl.objects.filter(item_id=item_id).first()

        if search_query:
            item_details = items.objects.filter(item_id=item_id, item_name__icontains=search_query).first()
        else:
            item_details = items.objects.filter(item_id=item_id).first()

        if item_details:
            total_stockQty = stock_qty

            # Check if total_stockQty is less than re_order_qty
            if item_details.re_order_qty and total_stockQty < float(item_details.re_order_qty):
                stock_details = stock_lists.objects.filter(item_id=item_id, store_id=selected_store_id).first()
                store_name = stock_details.store_id.store_name if stock_details else None

                serialized_item = {
                    'item_no': item_details.item_no,
                    'item_name': item_details.item_name,
                    'item_type': item_details.type_id.type_name,
                    'item_uom': item_details.item_uom_id.item_uom_name,
                    'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else None,
                    'item_Manufacturer': item_details.supplier_id.supplier_name,
                    'store_name': store_name,
                    'item_p_price': item_details.purchase_price,
                    'item_s_price': item_details.sales_price,
                    'total_stockQty': total_stockQty,
                }

                serialized_data.append(serialized_item)

    sorted_serialized_data = sorted(serialized_data, key=lambda x: x['total_stockQty'], reverse=True)

    return JsonResponse({'data': sorted_serialized_data})



