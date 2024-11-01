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
from deliver_chalan.models import delivery_Chalan_list
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def invoice_listAPI(request):
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

    return render(request, 'invoice_list/invoice_list.html', context)


@login_required()
@require_POST
def get_Invoice_listAPI(request):
    if request.method == "POST":
        start_date = request.POST.get('inv_start')
        end_date = request.POST.get('inv_end')
        org_id = request.POST.get('org_id')
        branch_id = request.POST.get('branch_id')

        inv_start_date, inv_end_date = None, None

        print(f"Received start_date: {start_date}, end_date: {end_date}")

        # Parse and validate date inputs
        if start_date and end_date:
            try:
                inv_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                inv_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

            try:
                invoices = invoice_list.objects.filter(
                    invoice_date__range=(inv_start_date, inv_end_date),
                    org_id=org_id,
                    branch_id=branch_id
                )
                invoice_details = invoicedtl_list.objects.all()
                payments = payment_list.objects.all()
                carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True)

                combined_data = []

                for invoice in invoices:
                    details = invoice_details.filter(inv_id=invoice)
                    payment = payments.filter(inv_id=invoice)
                    cost_buyer = carrying_cost_buyer.filter(inv_id=invoice)
                    delivery_data = delivery_Chalan_list.objects.filter(inv_id=invoice)

                    isCreated = any(delivery.is_created for delivery in delivery_data)

                    # Initialize totals
                    grand_total = sum(detail.sales_rate * detail.qty for detail in details)
                    grand_total_dis = round(sum(
                        (detail.item_w_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)
                        for detail in details
                    ), 2)
                    grand_total_gross_dis = round(sum(
                        (detail.gross_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)
                        for detail in details
                    ), 2)
                    total_discount_sum = round(grand_total_dis + grand_total_gross_dis, 2)

                    grand_vat_tax = round(sum(
                        (detail.gross_vat_tax / detail.qty) * (detail.qty - detail.is_cancel_qty)
                        for detail in details
                    ), 2)

                    grand_cancel_amt = round(sum(
                        detail.sales_rate * detail.is_cancel_qty for detail in details
                    ), 2)

                    total_cost_amt = sum(buyer.other_exps_amt for buyer in cost_buyer)

                    total_net_bill = round(
                        (grand_total + grand_vat_tax + total_cost_amt) - (total_discount_sum + grand_cancel_amt), 0
                    )

                    # Calculate collection, refund, and due amounts
                    total_collection_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "1")
                    total_due_collection = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "2")
                    total_refund_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "3")
                    total_adjust_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "4")

                    total_payment_collection = round(
                        total_collection_amt + total_due_collection + total_adjust_amt, 0
                    )

                    total_net_collection = total_payment_collection - total_refund_amt
                    total_due_amount = round(total_net_bill - total_net_collection, 0)

                    combined_data.append({
                        'invoice': {
                            'invoice_date': invoice.invoice_date,
                            'inv_id': invoice.inv_id,
                            'customer_name': invoice.customer_name,
                            'gender': invoice.gender,
                            'mobile_number': invoice.mobile_number,
                            'is_carrcost_notapp': invoice.is_carrcost_notapp,
                            'is_modified': invoice.is_modified_item,
                            'is_created': isCreated,
                        },
                        'grand_total': grand_total,
                        'grand_total_dis': grand_total_dis,
                        'grand_vat_tax': grand_vat_tax,
                        'grand_cancel_amt': grand_cancel_amt,
                        'total_net_bill': total_net_bill,
                        'total_collection_amt': total_collection_amt,
                        'total_due_collection': total_due_collection,
                        'total_refund_amt': total_refund_amt,
                        'total_adjust_amt': total_adjust_amt,
                        'total_payment_collection': total_payment_collection,
                        'grand_total_gross_dis': grand_total_gross_dis,
                        'total_discount_sum': total_discount_sum,
                        'total_due_amount': total_due_amount,
                        'total_cost_amt': total_cost_amt,
                    })

                return JsonResponse({'invoices': combined_data}, status=200, safe=False)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'error': 'Start date or end date is missing.'}, status=400)



# @login_required()
# @require_POST
# def get_Invoice_listAPI(request):
#     if request.method == "POST":
#         start_date = request.POST.get('inv_start')
#         end_date = request.POST.get('inv_end')
#         org_id = request.POST.get('org_id')
#         branch_id = request.POST.get('branch_id')

#         inv_start_date = None
#         inv_end_date = None

#         print(f"Received start_date: {start_date}, end_date: {end_date}")

#         # Check if details_start and details_end are not empty strings
#         if start_date and end_date:
#             try:
#                 # Convert date strings to datetime objects
#                 inv_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#                 inv_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

#             except ValueError:
#                 return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

#             try:
#                 invoices = invoice_list.objects.filter(invoice_date__range=(inv_start_date, inv_end_date), org_id=org_id, branch_id=branch_id).all()
#                 invoice_details = invoicedtl_list.objects.all()
#                 payments = payment_list.objects.all()
#                 carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True).all()

#                 combined_data = []

#                 for invoice in invoices:
#                     details = invoice_details.filter(inv_id=invoice).all()
#                     payment = payments.filter(inv_id=invoice).all()
#                     cost_buyer = carrying_cost_buyer.filter(inv_id=invoice).all()
#                     delivery_data = delivery_Chalan_list.objects.filter(inv_id=invoice).all()

#                     # Initialize the `isCreated` variable with a default value
#                     isCreated = False

#                     for delivery in delivery_data:
#                         isCreated = delivery.is_created

#                     # Initialize invoice-wise totals
#                     grand_total = 0
#                     grand_total_dis = 0
#                     grand_vat_tax = 0
#                     grand_cancel_amt = 0
#                     refund_amt_sum = 0
#                     total_collection_amt = 0
#                     total_due_collection = 0
#                     total_payment_collection = 0
#                     total_refund_amt = 0
#                     total_adjust_amt = 0
#                     grand_total_gross_dis = 0
#                     total_discount_sum = 0
#                     total_due_amount = 0
#                     total_cost_amt = 0
                    
#                     for buyer in cost_buyer:
#                         cost_amt = buyer.other_exps_amt
#                         total_cost_amt += cost_amt

#                     # Item rate over invoice items
#                     item_total = sum(detail.sales_rate * detail.qty for detail in details)
#                     grand_total += item_total

#                     # Discount calculation
#                     item_w_dis = sum(((detail.item_w_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)

#                     grand_total_dis += item_w_dis
#                     grand_total_dis = round(grand_total_dis, 2)

#                     total_gross_dis = sum(((detail.gross_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)

#                     grand_total_gross_dis += total_gross_dis
#                     grand_total_gross_dis = round(grand_total_gross_dis, 2)

#                     total_discount_sum = grand_total_dis + grand_total_gross_dis
#                     total_discount_sum = round(total_discount_sum, 2)

#                     # VAT tax calculation
#                     item_wise_total_vat_tax = sum(((detail.gross_vat_tax / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)

#                     grand_vat_tax += item_wise_total_vat_tax
#                     grand_vat_tax = round(grand_vat_tax, 2)

#                     # Cancel amount calculation
#                     total_item_cancel_amt = sum(detail.sales_rate * detail.is_cancel_qty for detail in details)
#                     grand_cancel_amt += total_item_cancel_amt
#                     grand_cancel_amt = round(grand_cancel_amt, 2)

#                     # Calculate total net bill for this invoice
#                     total_net_bill = ((grand_total + grand_vat_tax + total_cost_amt) - (total_discount_sum + grand_cancel_amt))
#                     total_net_bill = round(total_net_bill, 0)

#                     # Calculate collection, refund, and due amounts
#                     total_collection_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "1")
#                     total_due_collection = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "2")
#                     total_refund_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "3")
#                     total_adjust_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "4")

#                     total_payment_collection = round(
#                         total_collection_amt + total_due_collection + total_adjust_amt, 0
#                     )

#                     total_net_collection = total_payment_collection - total_refund_amt
#                     total_due_amount = round(total_net_bill - total_net_collection, 0)

#                     combined_data.append({
#                         'invoice': {
#                             'invoice_date': invoice.invoice_date,
#                             'inv_id': invoice.inv_id,
#                             'customer_name': invoice.customer_name,
#                             'gender': invoice.gender,
#                             'mobile_number': invoice.mobile_number,
#                             'is_carrcost_notapp': invoice.is_carrcost_notapp,
#                             'is_modified': invoice.is_modified_item,
#                             'is_created': isCreated,
#                             # Add other fields you need here
#                         },
#                         # 'invoice': invoice,
#                         'grand_total': grand_total,
#                         'grand_total_dis': grand_total_dis,
#                         'grand_vat_tax': grand_vat_tax,
#                         'grand_cancel_amt': grand_cancel_amt,
#                         'refund_amt_sum': refund_amt_sum,
#                         'total_net_bill': total_net_bill,
#                         'total_collection_amt': total_collection_amt,
#                         'total_due_collection': total_due_collection,
#                         'total_refund_amt': total_refund_amt,
#                         'total_payment_collection': total_payment_collection,
#                         'grand_total_gross_dis': grand_total_gross_dis,
#                         'total_discount_sum': total_discount_sum,
#                         'total_due_amount': total_due_amount,
#                         'total_cost_amt': total_cost_amt,
#                     })

#                 return JsonResponse({'data': combined_data})

#             except ValueError as e:
#                 return JsonResponse({'error': 'Invalid date format'})
#         else:
#              return JsonResponse({'error': 'Invalid date format or missing date'})
        
#     return JsonResponse({'error': 'Invalid request method'})



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
