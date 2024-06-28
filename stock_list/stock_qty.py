import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField
from django.db import models
from django.http import HttpResponse, JsonResponse
from stock_list.models import stock_lists
from item_setup.models import item_supplierdtl, items
from store_setup.models import store
from organizations.models import organizationlst
from po_return.models import po_return_details
from supplier_setup.models import suppliers
from item_pos.models import invoicedtl_list
from django.contrib.auth import get_user_model
User = get_user_model()


def get_available_qty(item_id, store_id, org_id):
    try:
        # Aggregate stock quantities directly in the query
        stock_total_qty = stock_lists.objects.filter(
            is_approved=True, item_id=item_id, store_id=store_id
        ).aggregate(total_stock_qty=Sum('stock_qty'))['total_stock_qty'] or 0

        # Aggregate sales quantities directly in the query
        sales_total_qty = invoicedtl_list.objects.filter(
            item_id=item_id, store_id=store_id
        ).aggregate(
            sales_total_qty=Sum(ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField()))
        )['sales_total_qty'] or 0

        # Aggregate return quantities directly in the query
        tot_return_qty = po_return_details.objects.filter(
            item_id=item_id, store_id=store_id
        ).aggregate(
            tot_return_qty=Sum(ExpressionWrapper(F('return_qty'), output_field=IntegerField()))
        )['tot_return_qty'] or 0

        available_qty = stock_total_qty - (sales_total_qty + tot_return_qty)
        return available_qty
    
    except Exception as e:
        print(f"Error calculating available quantity: {str(e)}")
        return 0