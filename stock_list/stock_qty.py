import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField
from django.db import models
from django.http import HttpResponse, JsonResponse
from stock_list.models import in_stock
from django.contrib.auth import get_user_model
User = get_user_model()


def get_available_qty(item_id, store_id, org_id):
    try:
        # Aggregate stock quantities directly in the query
        available_qty = in_stock.objects.filter(item_id=item_id, store_id=store_id).first()

        # Check if the stock record exists and return the quantity
        if available_qty:
            return available_qty.stock_qty
        else:
            return 0
    
    except Exception as e:
        print(f"Error calculating available quantity: {str(e)}")
        return 0
    

# def get_available_qty(item_id, store_id, org_id):
#     try:
#         # Aggregate stock quantities directly in the query
#         stock_total_qty = stock_lists.objects.filter(
#             is_approved=True, item_id=item_id, store_id=store_id
#         ).aggregate(total_stock_qty=Sum('stock_qty'))['total_stock_qty'] or 0

#         # Aggregate sales quantities directly in the query
#         sales_total_qty = invoicedtl_list.objects.filter(
#             item_id=item_id, store_id=store_id
#         ).aggregate(
#             sales_total_qty=Sum(ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField()))
#         )['sales_total_qty'] or 0

#         # Aggregate return quantities directly in the query
#         tot_return_qty = po_return_details.objects.filter(
#             item_id=item_id, store_id=store_id
#         ).aggregate(
#             tot_return_qty=Sum(ExpressionWrapper(F('return_qty'), output_field=IntegerField()))
#         )['tot_return_qty'] or 0

#         available_qty = stock_total_qty - (sales_total_qty + tot_return_qty)
#         return available_qty
    
#     except Exception as e:
#         print(f"Error calculating available quantity: {str(e)}")
#         return 0