import sys
import json
from num2words import num2words
from pickle import FALSE
from datetime import datetime
from django.db.models import Q, Sum
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def invoice_listAPI(request):

    return render(request, 'invoice_list/invoice_list.html')


@login_required()
@require_POST
def get_Invoice_listAPI(request):
    if request.method == "POST":
        start_date = request.POST.get('inv_start')
        end_date = request.POST.get('inv_end')

        inv_start_date = None
        inv_end_date = None

        print(f"Received start_date: {start_date}, end_date: {end_date}")

        # Check if details_start and details_end are not empty strings
        if start_date and end_date:
            try:
                # Convert date strings to datetime objects
                inv_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                inv_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

            try:
                invoices = invoice_list.objects.filter(invoice_date__range=(inv_start_date, inv_end_date)).all()
                invoice_details = invoicedtl_list.objects.all()
                payments = payment_list.objects.all()
                carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True).all()

                combined_data = []

                for invoice in invoices:
                    details = invoice_details.filter(inv_id=invoice).all()
                    payment = payments.filter(inv_id=invoice).all()
                    cost_buyer = carrying_cost_buyer.filter(inv_id=invoice).all()

                    # Initialize invoice-wise totals
                    grand_total = 0
                    grand_total_dis = 0
                    grand_vat_tax = 0
                    grand_cancel_amt = 0
                    refund_amt_sum = 0
                    total_collection_amt = 0
                    total_due_collection = 0
                    total_payment_collection = 0
                    total_refund_amt = 0
                    grand_total_gross_dis = 0
                    total_discount_sum = 0
                    total_due_amount = 0
                    total_cost_amt = 0
                    
                    for buyer in cost_buyer:
                        cost_amt = buyer.other_exps_amt
                        total_cost_amt += cost_amt

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
                    total_discount_sum = round(total_discount_sum, 2)

                    # VAT tax calculation
                    item_wise_total_vat_tax = sum(((detail.gross_vat_tax / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)

                    grand_vat_tax += item_wise_total_vat_tax
                    grand_vat_tax = round(grand_vat_tax, 2)

                    # Cancel amount calculation
                    total_item_cancel_amt = sum(detail.sales_rate * detail.is_cancel_qty for detail in details)
                    grand_cancel_amt += total_item_cancel_amt

                    # Calculate total net bill for this invoice
                    total_net_bill = ((grand_total + grand_vat_tax + total_cost_amt) - (total_discount_sum + grand_cancel_amt))
                    total_net_bill = round(total_net_bill, 0)

                    # Calculate total collection amount and total due amount
                    for pay in payment:
                        if pay.collection_mode == "1":
                            total_collection_amt += float(pay.pay_amt)
                        elif pay.collection_mode == "2":
                            total_due_collection += float(pay.pay_amt)
                        elif pay.collection_mode == "3":
                            total_refund_amt += float(pay.pay_amt)

                        total_payment_collection = total_collection_amt + total_due_collection
                        total_payment_collection = round(
                            total_payment_collection, 0)

                        # due amount
                        total_net_collection = total_payment_collection - total_refund_amt
                        total_due_amount = total_net_bill - total_net_collection
                        total_due_amount = round(total_due_amount, 0)

                    combined_data.append({
                        'invoice': {
                            'invoice_date': invoice.invoice_date,
                            'inv_id': invoice.inv_id,
                            'customer_name': invoice.customer_name,
                            'gender': invoice.gender,
                            'mobile_number': invoice.mobile_number,
                            # Add other fields you need here
                        },
                        # 'invoice': invoice,
                        'grand_total': grand_total,
                        'grand_total_dis': grand_total_dis,
                        'grand_vat_tax': grand_vat_tax,
                        'grand_cancel_amt': grand_cancel_amt,
                        'refund_amt_sum': refund_amt_sum,
                        'total_net_bill': total_net_bill,
                        'total_collection_amt': total_collection_amt,
                        'total_due_collection': total_due_collection,
                        'total_refund_amt': total_refund_amt,
                        'total_payment_collection': total_payment_collection,
                        'grand_total_gross_dis': grand_total_gross_dis,
                        'total_discount_sum': total_discount_sum,
                        'total_due_amount': total_due_amount,
                        'total_cost_amt': total_cost_amt,
                    })

                return JsonResponse({'data': combined_data})

            except ValueError as e:
                return JsonResponse({'error': 'Invalid date format'})
        else:
             return JsonResponse({'error': 'Invalid date format or missing date'})
        
    return JsonResponse({'error': 'Invalid request method'})


# @login_required()
# def invoice_listAPI(request):

#     if request.method == "POST":
#         resp = {'status': 'failed', 'msg': ''}

#     start_date = None
#     end_date = None
#     # Initialize the grand total
#     grand_total = 0
#     grand_total_dis = 0
#     item_w_total_dis = 0
#     gross_total_dis = 0
#     grand_vat_tax = 0
#     grand_cancel_amt = 0
#     refund_amt_sum = 0
#     total_net_bill = 0
#     total_collection_amt = 0
#     total_due_amt = 0

#     combined_data = []

#     if request.method == "POST":
#         start_date = request.POST.get('start_date')
#         end_date = request.POST.get('end_date')

#         # Parse the dates from the request POST data
#         start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#         end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

#         # Query data from your models
#         invoices = invoice_list.objects.filter(invoice_date__range=(start_date, end_date)).all()
#         invoice_details = invoicedtl_list.objects.all()
#         payments = payment_list.objects.all()

#         for invoice in invoices:
#             details = invoice_details.filter(inv_id=invoice).all()
#             payment = payments.filter(inv_id=invoice).all()

#             # Item rate over invoice items
#             item_total = sum(detail.sales_rate * detail.qty for detail in details)
#             item_total = round(item_total, 2)
#             grand_total += item_total

#             # discount calculation
#             item_w_dis = sum(((detail.item_w_dis / detail.qty) * ( detail.qty - detail.is_cancel_qty)) for detail in details)
#             item_w_dis = round(item_w_dis, 2)
#             item_gross_dis = sum((detail.gross_dis / detail.qty) * ( detail.qty - detail.is_cancel_qty) for detail in details)
#             item_gross_dis = round(item_gross_dis, 2)
#             item_w_total_dis += item_w_dis
#             gross_total_dis += item_gross_dis
#             grand_total_dis = item_w_total_dis + gross_total_dis

#             #  vat tax calculation
#             item_wise_total_vat_tax = sum(((detail.gross_vat_tax / detail.qty) * ( detail.qty - detail.is_cancel_qty)) for detail in details)
#             item_wise_total_vat_tax = round(item_wise_total_vat_tax, 2)
#             grand_vat_tax += item_wise_total_vat_tax

#             # cancel amount calculation
#             total_item_cancel_amt = sum(detail.sales_rate * detail.is_cancel_qty for detail in details)
#             total_item_cancel_amt = round(total_item_cancel_amt, 2)
#             grand_cancel_amt += total_item_cancel_amt

#             # total net bill
#             total_net_bill = ((grand_total + grand_vat_tax) - (grand_total_dis + grand_cancel_amt))
#             total_net_bill = round(total_net_bill, 2)


#             # pay amount value and find out due value
#             # Filter PayList for collection_mode="1" and sum the payments
#             collection_amt = payment.filter(collection_mode="1")
#             collection_amt_result = collection_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
#             if collection_amt_result['pay_amt_sum'] is not None:
#                 collection_amt_sum = collection_amt_result['pay_amt_sum']
#             else:
#                 collection_amt_sum = 0.0

#             # Filter PayList for collection_mode="2" and sum the payments
#             due_collection_amt = payment.filter(collection_mode="2")
#             due_collection_amt_result = due_collection_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
#             if due_collection_amt_result['pay_amt_sum'] is not None:
#                 due_collection_amt_sum = due_collection_amt_result['pay_amt_sum']
#             else:
#                 due_collection_amt_sum = 0.0


#             # Filter PayList for collection_mode="3" and sum the payments
#             refund_amt = payment.filter(collection_mode="3")
#             refund_amt_result = refund_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
#             if refund_amt_result['pay_amt_sum'] is not None:
#                 refund_amt_sum = refund_amt_result['pay_amt_sum']
#             else:
#                 refund_amt_sum = 0.0

#             # total payment = collection + due collection - refund
#             total_collection_amt = collection_amt_sum + due_collection_amt_sum
#             total_collection_amt = round(total_collection_amt, 2)


#             # total due amount
#             total_due_amt = total_net_bill - (total_collection_amt - refund_amt_sum)
#             total_due_amt = round(total_due_amt, 2)


#             combined_data.append({
#                 'invoice': invoice,
#                 'payment': payment,
#                 'grand_total': grand_total,
#                 'grand_total_dis': grand_total_dis,
#                 'grand_vat_tax': grand_vat_tax,
#                 'grand_cancel_amt': grand_cancel_amt,
#                 'refund_amt_sum': refund_amt_sum,
#                 'total_net_bill': total_net_bill,
#                 'total_collection_amt': total_collection_amt,
#                 'total_due_amt': total_due_amt,
#             })
#     else:
#         # If not a POST request or no date range specified, retrieve all invoices
#         combined_data = []

#     return render(request, 'invoice_list/invoice_list.html', {'combined_data': combined_data})


@login_required()
def testingInvoiceListAPI(request):

    if request.method == "POST":
        resp = {'status': 'failed', 'msg': ''}
    start_date = None
    end_date = None

    combined_data = []

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Parse the dates from the request POST data
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Query data from your models
        invoices = invoice_list.objects.filter(
            invoice_date__range=(start_date, end_date)).all()
        invoice_details = invoicedtl_list.objects.all()
        payments = payment_list.objects.all()

        for invoice in invoices:
            details = invoice_details.filter(inv_id=invoice).first()
            payment = payments.filter(inv_id=invoice).first()

            # Calculate sales_rate_sum using aggregate on the queryset
            sales_rate_sum = invoice_details.filter(inv_id=invoice).aggregate(
                sales_rate_sum=Sum('sales_rate'))['sales_rate_sum']
            qty_sum = invoice_details.filter(inv_id=invoice).aggregate(
                qty_sum=Sum('qty'))['qty_sum']

            combined_data.append({
                'invoice': invoice,
                'details': details,
                'payment': payment,
                'sales_rate_sum': sales_rate_sum,
                'qty_sum': qty_sum,
            })
    else:
        # If not a POST request or no date range specified, retrieve all invoices
        combined_data = []

    return render(request, 'invoice_list/testing_invoice_list.html', {'combined_data': combined_data})
