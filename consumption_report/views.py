import sys
import json
from num2words import num2words
from datetime import date, datetime
from pickle import FALSE
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from django.db import models
from django.db import transaction
from itertools import groupby
from collections import defaultdict
from operator import itemgetter, attrgetter
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from store_setup.models import store
from item_pos.models import invoice_list, invoicedtl_list
from item_setup.models import items, item_supplierdtl
from stock_list.models import stock_lists
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def consumptionReportManagerAPI(request):
    store_data = store.objects.filter(
        is_main_store=True).all().order_by('store_name')
    stock_batch = stock_lists.objects.filter(is_approved=True).values(
        'item_batch').annotate(count=Count('item_batch')).order_by('item_batch')

    context = {
        'store_data': store_data,
        'stock_batch': stock_batch,
    }

    return render(request, 'item_consumption/item_consumption_manager.html', context)


# details consumptions
@login_required
def getconsumptionDetailsAPI(request):
    if request.method == 'GET':
        selected_store_id = request.GET.get('store_id')
        # selected_batch = request.GET.get('item_batch')
        details_start = request.GET.get('details_start')
        details_end = request.GET.get('details_end')

        start_date = None
        end_date = None

        # Check if details_start and details_end are not empty strings
        if details_start and details_end:
            try:
                # Convert date strings to datetime objects
                start_date = datetime.strptime(details_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(details_end, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        invoice_data = []

        # Fetching invoice details based on the selected criteria
        invoice_details = invoicedtl_list.objects.all().order_by('inv_id')

        # Filter by selected store_id if it's not "All Store" (value="1")
        if selected_store_id and selected_store_id != "1":
            invoice_details = invoice_details.filter(
                store_id=selected_store_id)

        # Filter by selected batch if it's not "All Batch" (value="1")
        # if selected_batch and selected_batch != "1":
        #     invoice_details = invoice_details.filter(
        #         stock_id__item_batch=selected_batch)

        # Filter by date range if both start_date and end_date are valid
        if start_date and end_date:
            invoice_details = invoice_details.filter(
                inv_id__invoice_date__range=[start_date, end_date])

        unique_invoice_ids = invoice_details.values_list(
            'inv_id', flat=True).distinct()

        total_consumption_sum = 0

        for inv_id_value in unique_invoice_ids:
            # Fetch invoice information for each unique inv_id
            invoice = invoice_list.objects.filter(inv_id=inv_id_value).first()

            if invoice:
                invoice_item = {
                    'invoice_id': invoice.inv_id,
                    'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
                    'customer_name': invoice.customer_name,
                    'gender': invoice.gender,
                    'mobile_number': invoice.mobile_number,
                    'details': []
                }

                # Find related invoice details for this inv_id
                related_details = invoice.invoicedtl_list_set.all()
                total_consumption = 0

                for detail in related_details:

                    total_cons = detail.qty - detail.is_cancel_qty
                    total_consumption += total_cons

                    invoice_item['details'].append({
                        'item_name': detail.item_id.item_name,
                        'store_name': detail.store_id.store_name,
                        # 'item_batch': detail.stock_id.item_batch,
                        # 'stock_qty': detail.stock_id.stock_qty,
                        'sales_qty': detail.qty,
                        'cancel_qty': detail.is_cancel_qty,
                        'consumption_qty': total_cons,
                        'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d')
                    })

                invoice_item['grand_total'] = total_consumption
                invoice_data.append(invoice_item)
                total_consumption_sum += total_consumption

        return JsonResponse({'invoice_data': invoice_data, 'total_consumption_sum': total_consumption_sum})

    return JsonResponse({'error': 'Invalid request'})


# summary consumptions
@login_required
def getconsumptionSummaryAPI(request):
    store_id = request.GET.get('store_id')
    summary_start = request.GET.get('summary_start')
    summary_end = request.GET.get('summary_end')

    start_date = None
    end_date = None

    # Check if details_start and details_end are not empty strings
    if summary_start and summary_end:
        try:
            # Convert date strings to datetime objects
            start_date = datetime.strptime(summary_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(summary_end, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    # If store_id is None or '1' (for all stores), get consumption summary for all stores
    if store_id is None or store_id == '1':
        invoice_details = invoicedtl_list.objects.filter(
            inv_id__invoice_date__range=[start_date, end_date]  # Filter by date range
        ).values(
            'item_id__item_no',
            'item_id__item_name',
            'store_id__store_name',
            'stock_id__item_batch'
        ).annotate(
            total_sales_qty=Sum('qty'),
            total_cancel_qty=Sum('is_cancel_qty')
        )
    else:
        # Filter invoices for the selected store ID and date range
        invoice_details = invoicedtl_list.objects.filter(
            store_id=store_id,
            inv_id__invoice_date__range=[start_date, end_date]  # Filter by date range
        ).values(
            'item_id__item_no',
            'item_id__item_name',
            'store_id__store_name',
            'stock_id__item_batch'
        ).annotate(
            total_sales_qty=Sum('qty'),
            total_cancel_qty=Sum('is_cancel_qty')
        )

    cons_summary = []
    grand_total = 0

    for detail in invoice_details:
        total_cons = detail['total_sales_qty'] - detail['total_cancel_qty']
        grand_total += total_cons
        cons_summary.append({
            'item_no': detail['item_id__item_no'],
            'item_name': detail['item_id__item_name'],
            'store_name': detail['store_id__store_name'],
            'item_batch': detail['stock_id__item_batch'],
            'sales_qty': detail['total_sales_qty'],
            'cancel_qty': detail['total_cancel_qty'],
            'total_cons': total_cons,
        })

    cons_summary.append({
        'grand_total': grand_total
    })

    return JsonResponse({'data': cons_summary})
