import sys
import json
from num2words import num2words
from pickle import FALSE
from datetime import datetime
from django.db.models import Q, F, Sum, Count
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms.models import model_to_dict
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from item_setup.models import items
from stock_list.models import in_stock
from store_setup.models import store
from bank_statement.models import cash_on_hands
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.
@login_required()
def dueRefundManageAPI(request):

    return render(request, 'due_refund_col/can_due_refund_manager.html')


# Invoice cancel data view
@login_required()
def invoiceCancelDetailsAPI(request, inv_id):
   
    try:
        # Retrieve the invoice based on inv_id or return a 404 error if not found
        invoice = get_object_or_404(invoice_list, inv_id=inv_id)

        # Retrieve the related invoicedtl data based on inv_id
        invoicedtl_data = invoicedtl_list.objects.filter(inv_id=inv_id)

        # Retrieve payments related to the invoice
        payments = payment_list.objects.filter(inv_id=invoice)
        # carrying cost buyer wise
        carrying_cost = rent_others_exps.objects.filter(inv_id=invoice)

        # Initialize lists to store invoicedtl data, invoice data, and payments amounts
        invoicedtl_items = []
        invoice_items = []
        payments_amt = {}

        grand_total_bill = 0
        grand_cancel_bill = 0
        grand_cancel_vat = 0
        grand_cancel_gross_dis = 0
        total_vat_tax = 0
        total_gross_dis = 0
        total_seller_carrying = 0
        total_buyer_carrying = 0
        
        for carrying in carrying_cost:
            if carrying.is_seller==True:
                total_seller_carrying += carrying.other_exps_amt
            if carrying.is_buyer==True:
                total_buyer_carrying += carrying.other_exps_amt

        # Create a list of dictionaries containing invoicedtl data
        for item in invoicedtl_data:
            cancel_item_w_dis = (item.item_w_dis / item.qty) * item.is_cancel_qty

            total_bill = (item.sales_rate * item.qty) - item.item_w_dis
            cancel_bill = (item.sales_rate * item.is_cancel_qty) - cancel_item_w_dis
            cancel_vat = (item.gross_vat_tax / item.qty) * item.is_cancel_qty
            cancel_gross_dis = (item.gross_dis / item.qty) * item.is_cancel_qty

            total_vat_tax += item.gross_vat_tax
            total_gross_dis += item.gross_dis

            invoicedtl_items.append({
                'invdtl_id': item.invdtl_id,
                'item_no': item.item_id.item_no,
                'item_name': item.item_id.item_name,
                'item_type': item.item_id.type_id.type_name,
                # 'batch': item.stock_id.item_batch,
                'item_w_dis': item.item_w_dis,
                'gross_dis': item.gross_dis,
                'vat_tax': item.gross_vat_tax,
                'sales_rate': item.sales_rate,
                'qty': item.qty,
                'canncelled_qty': item.is_cancel_qty,
                'cancel_reason': item.cancel_reason,
                'total_bill': total_bill,
                'total_dis': item.gross_dis,
                'cancel_bill': cancel_bill,
                'cancel_vat': cancel_vat,
                'cancel_gross_dis': cancel_gross_dis,
                'total_seller_carrying': total_seller_carrying,
                'total_buyer_carrying': total_buyer_carrying,
            })

            # Update the grand totals
            grand_total_bill += total_bill
            grand_cancel_bill += cancel_bill
            grand_cancel_vat += cancel_vat
            grand_cancel_gross_dis += cancel_gross_dis

        # Calculate payment sums
        collection_amt = payments.filter(collection_mode="1").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        due_collection_amt = payments.filter(collection_mode="2").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        adjust_collection_amt = payments.filter(collection_mode="4").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        refund_amt = payments.filter(collection_mode="3").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0

        grand_vat_tax = total_vat_tax - grand_cancel_vat
        grand_discount = total_gross_dis - grand_cancel_gross_dis

        grand_net_bill = (grand_total_bill + grand_vat_tax + total_buyer_carrying) - (grand_cancel_bill + grand_discount)
        grand_net_bill = round(grand_net_bill, 0)

        grand_net_coll = (collection_amt + due_collection_amt + adjust_collection_amt) - refund_amt
        net_due_amt = grand_net_bill - grand_net_coll
        net_due_amt = round(net_due_amt, 0)

        # Create a context dictionary with the data
        invoice_items.append({
            'inv_id': invoice.inv_id,
            'org_id': invoice.org_id.org_id if invoice.org_id else None,
            'org_name': invoice.org_id.org_name if invoice.org_id else None,
            'branch_id': invoice.branch_id.branch_id if invoice.branch_id else None,
            'branch_name': invoice.branch_id.branch_name if invoice.branch_id else None,
            'supplier_id': invoice.supplier_id.supplier_id if invoice.supplier_id else None,
            'supplier_name': invoice.supplier_id.supplier_name if invoice.supplier_id else None,
            'invoice_date': invoice.invoice_date,
            'customer_name': invoice.customer_name,
            'gender': invoice.gender,
            'mobile_number': invoice.mobile_number,
            # Add other invoice fields as needed
        })

        payments_amt = [{
            'collection_amt_sum': collection_amt,
            'due_collection_amt_sum': due_collection_amt,
            'adjust_collection_amt': adjust_collection_amt,
            'refund_amt_sum': refund_amt,
            'grand_net_bill': grand_net_bill,
            'grand_net_coll': grand_net_coll,
            'net_due_amt': net_due_amt,
        }]

        context = {
            'invoice_items': invoice_items,
            'invoicedtl_data': invoicedtl_items,
            'payments_amt': payments_amt,
        }

        # Return the data as a JSON response
        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})


@login_required()
def invoiceCancelAPI(request):
    resp = {'success': False, 'errmsg': 'Update Invoice details Fail'}

    data = request.POST
    inv_id = data.get('can_searchID')

    if inv_id and inv_id.isnumeric() and int(inv_id) > 0:
        invdtl_ids = data.getlist("invoicedtl_id[]")
        net_cancel_qtys = data.getlist('net_cancelQty[]')
        cancel_reasons = data.getlist('cancel_reason[]')

        try:
            for invdtl_id, cancel_qty, inv_cancel_reason in zip(invdtl_ids, net_cancel_qtys, cancel_reasons):
                inv_id_instance = get_object_or_404(invoice_list, pk=inv_id)
                inv_dtl_id = int(invdtl_id)

                try:
                    # Retrieve the invoicedtl instance
                    invoicedtl_instance = get_object_or_404(invoicedtl_list, inv_id=inv_id_instance, invdtl_id=inv_dtl_id)
                    store_instance = invoicedtl_instance.store_id
                    item_instance = invoicedtl_instance.item_id

                    # Update the specific invoicedtl instance
                    invoicedtl_instance.is_cancel_qty = cancel_qty
                    invoicedtl_instance.cancel_reason = inv_cancel_reason
                    invoicedtl_instance.ss_modifier = request.user
                    invoicedtl_instance.save()

                    # Update or create in_stock entry
                    in_stock_obj, created = in_stock.objects.get_or_create(
                        item_id=item_instance,
                        store_id=store_instance,
                        defaults={
                            'stock_qty': cancel_qty,  # If new, set to the canceled quantity
                        }
                    )

                    if not created:
                        # If the in_stock entry exists, update the stock quantity by adding the canceled amount
                        in_stock_obj.stock_qty += float(cancel_qty)
                        in_stock_obj.save()

                except Exception as update_error:
                    # Log any update errors or handle them as needed
                    print(f"Error updating invdtl_id {inv_dtl_id}: {update_error}")

        except Exception as e:
            resp['errmsg'] = str(e)
            return JsonResponse(resp)

        resp = {'success': True, 'msg': 'Successful!'}

    return JsonResponse(resp)


# item wise invoice cancel view
@login_required()
def getInvoiceDataAPI(request, inv_id):
    
    try:
        # Retrieve the invoice based on inv_id or return a 404 error if not found
        invoice = get_object_or_404(invoice_list, inv_id=inv_id)

        # Retrieve the related invoicedtl data based on inv_id
        invoicedtl_data = invoicedtl_list.objects.filter(inv_id=inv_id)

        # Retrieve payments related to the invoice
        payments = payment_list.objects.filter(inv_id=invoice)
        # carrying cost buyer wise
        carrying_cost = rent_others_exps.objects.filter(inv_id=invoice)

        # Initialize lists to store invoicedtl data, invoice data, and payments amounts
        invoicedtl_items = []
        invoice_items = []
        payments_amt = {}

        grand_total_bill = 0
        grand_cancel_bill = 0
        grand_cancel_vat = 0
        grand_cancel_gross_dis = 0
        total_vat_tax = 0
        total_gross_dis = 0
        total_seller_carrying = 0
        total_buyer_carrying = 0
        
        for carrying in carrying_cost:
            if carrying.is_seller==True:
                total_seller_carrying += carrying.other_exps_amt
            if carrying.is_buyer==True:
                total_buyer_carrying += carrying.other_exps_amt

        # Create a list of dictionaries containing invoicedtl data
        for item in invoicedtl_data:
            cancel_item_w_dis = (item.item_w_dis / item.qty) * item.is_cancel_qty

            total_bill = (item.sales_rate * item.qty) - item.item_w_dis
            cancel_bill = (item.sales_rate * item.is_cancel_qty) - cancel_item_w_dis
            cancel_vat = (item.gross_vat_tax / item.qty) * item.is_cancel_qty
            cancel_gross_dis = (item.gross_dis / item.qty) * item.is_cancel_qty

            total_vat_tax += item.gross_vat_tax
            total_gross_dis += item.gross_dis

            invoicedtl_items.append({
                'invdtl_id': item.invdtl_id,
                'item_no': item.item_id.item_no,
                'item_name': item.item_id.item_name,
                'item_type': item.item_id.type_id.type_name,
                # 'batch': item.stock_id.item_batch,
                'item_w_dis': item.item_w_dis,
                'gross_dis': item.gross_dis,
                'vat_tax': item.gross_vat_tax,
                'sales_rate': item.sales_rate,
                'qty': item.qty,
                'canncelled_qty': item.is_cancel_qty,
                'cancel_reason': item.cancel_reason,
                'total_bill': total_bill,
                'total_dis': item.gross_dis,
                'cancel_bill': cancel_bill,
                'cancel_vat': cancel_vat,
                'cancel_gross_dis': cancel_gross_dis,
                'total_seller_carrying': total_seller_carrying,
                'total_buyer_carrying': total_buyer_carrying,
            })

            # Update the grand totals
            grand_total_bill += total_bill
            grand_cancel_bill += cancel_bill
            grand_cancel_vat += cancel_vat
            grand_cancel_gross_dis += cancel_gross_dis

        # Calculate payment sums
        collection_amt = payments.filter(collection_mode="1").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        due_collection_amt = payments.filter(collection_mode="2").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        adjust_collection_amt = payments.filter(collection_mode="4").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        refund_amt = payments.filter(collection_mode="3").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0

        grand_vat_tax = total_vat_tax - grand_cancel_vat
        grand_discount = total_gross_dis - grand_cancel_gross_dis

        grand_net_bill = (grand_total_bill + grand_vat_tax + total_buyer_carrying) - (grand_cancel_bill + grand_discount)
        grand_net_bill = round(grand_net_bill, 0)

        grand_net_coll = (collection_amt + due_collection_amt + adjust_collection_amt) - refund_amt
        net_due_amt = grand_net_bill - grand_net_coll
        net_due_amt = round(net_due_amt, 0)

        # Create a context dictionary with the data
        invoice_items.append({
            'inv_id': invoice.inv_id,
            'org_id': invoice.org_id.org_id if invoice.org_id else None,
            'org_name': invoice.org_id.org_name if invoice.org_id else None,
            'branch_id': invoice.branch_id.branch_id if invoice.branch_id else None,
            'branch_name': invoice.branch_id.branch_name if invoice.branch_id else None,
            'supplier_id': invoice.supplier_id.supplier_id if invoice.supplier_id else None,
            'supplier_name': invoice.supplier_id.supplier_name if invoice.supplier_id else None,
            'invoice_date': invoice.invoice_date,
            'customer_name': invoice.customer_name,
            'gender': invoice.gender,
            'mobile_number': invoice.mobile_number,
            # Add other invoice fields as needed
        })

        payments_amt = [{
            'collection_amt_sum': collection_amt,
            'due_collection_amt_sum': due_collection_amt,
            'adjust_collection_amt': adjust_collection_amt,
            'refund_amt_sum': refund_amt,
            'grand_net_bill': grand_net_bill,
            'grand_net_coll': grand_net_coll,
            'net_due_amt': net_due_amt,
        }]

        context = {
            'invoice_items': invoice_items,
            'invoicedtl_data': invoicedtl_items,
            'payments_amt': payments_amt,
        }

        # Return the data as a JSON response
        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# item wise invoice cancel update API 
@login_required()
def updateInvoiceCancelAPI(request):
    resp = {'success': False, 'errmsg': 'Update Invoice details Fail'}

    data = request.POST
    inv_id = data.get('searchID')

    if inv_id and inv_id.isnumeric() and int(inv_id) > 0:
        invdtl_ids = data.getlist("invoicedtl_id[]")
        net_cancel_qtys = data.getlist('net_cancelQty[]')
        cancel_reasons = data.getlist('cancel_reason[]')

        try:
            for invdtl_id, cancel_qty, inv_cancel_reason in zip(invdtl_ids, net_cancel_qtys, cancel_reasons):
                inv_id_instance = get_object_or_404(invoice_list, pk=inv_id)
                inv_dtl_id = int(invdtl_id)

                try:
                    # Retrieve the invoicedtl instance
                    invoicedtl_instance = get_object_or_404(invoicedtl_list, inv_id=inv_id_instance, invdtl_id=inv_dtl_id)
                    store_instance = invoicedtl_instance.store_id
                    item_instance = invoicedtl_instance.item_id
                    
                    # Update the specific invoicedtl instance
                    invoicedtl_instance.is_cancel_qty = cancel_qty
                    invoicedtl_instance.cancel_reason = inv_cancel_reason
                    invoicedtl_instance.ss_modifier = request.user
                    invoicedtl_instance.save()

                    # Update or create in_stock entry
                    in_stock_obj, created = in_stock.objects.get_or_create(
                        item_id=item_instance,
                        store_id=store_instance,
                        defaults={
                            'stock_qty': cancel_qty,  # If new, set to the canceled quantity
                        }
                    )

                    if not created:
                        # If the in_stock entry exists, update the stock quantity by adding the canceled amount
                        in_stock_obj.stock_qty += float(cancel_qty)
                        in_stock_obj.save()


                except Exception as update_error:
                    # Log any update errors or handle them as needed
                    print(f"Error updating invdtl_id {inv_dtl_id}: {update_error}")

        except Exception as e:
            resp['errmsg'] = str(e)
            return JsonResponse(resp)

        resp = {'success': True, 'msg': 'Successful!'}

    return JsonResponse(resp)


# due refund collection data view
@login_required()
def getDueRefundDataAPI(request, inv_id):
    
    try:
        # Retrieve the invoice based on inv_id or return a 404 error if not found
        invoice = get_object_or_404(invoice_list, inv_id=inv_id)

        # Retrieve the related invoicedtl data based on inv_id
        invoicedtl_data = invoicedtl_list.objects.filter(inv_id=inv_id)
        invoicedtl_count = invoicedtl_list.objects.filter(inv_id=inv_id).count()

        # Retrieve payments related to the invoice
        payments = payment_list.objects.filter(inv_id=invoice)
        # carrying cost buyer wise
        carrying_cost = rent_others_exps.objects.filter(inv_id=invoice)

        # Initialize lists to store invoicedtl data, invoice data, and payments amounts
        invoicedtl_items = []
        invoice_items = []
        payments_amt = {}

        grand_total_bill = 0
        grand_cancel_bill = 0
        grand_cancel_vat = 0
        grand_cancel_gross_dis = 0
        total_vat_tax = 0
        total_gross_dis = 0
        total_seller_carrying = 0
        total_buyer_carrying = 0
        
        for carrying in carrying_cost:
            if carrying.is_seller==True:
                total_seller_carrying += carrying.other_exps_amt
            if carrying.is_buyer==True:
                total_buyer_carrying += carrying.other_exps_amt

        # Create a list of dictionaries containing invoicedtl data
        for item in invoicedtl_data:
            cancel_item_w_dis = (item.item_w_dis / item.qty) * item.is_cancel_qty

            total_bill = (item.sales_rate * item.qty) - item.item_w_dis
            cancel_bill = (item.sales_rate * item.is_cancel_qty) - cancel_item_w_dis
            cancel_vat = (item.gross_vat_tax / item.qty) * item.is_cancel_qty
            cancel_gross_dis = (item.gross_dis / item.qty) * item.is_cancel_qty

            total_vat_tax += item.gross_vat_tax
            total_gross_dis += item.gross_dis

            invoicedtl_items.append({
                'invdtl_id': item.invdtl_id,
                'item_no': item.item_id.item_no,
                'item_name': item.item_id.item_name,
                'item_type': item.item_id.type_id.type_name,
                # 'batch': item.stock_id.item_batch,
                'item_w_dis': item.item_w_dis,
                'gross_dis': item.gross_dis,
                'vat_tax': item.gross_vat_tax,
                'sales_rate': item.sales_rate,
                'qty': item.qty,
                'canncelled_qty': item.is_cancel_qty,
                'cancel_reason': item.cancel_reason,
                'total_bill': total_bill,
                'total_dis': item.gross_dis,
                'cancel_bill': cancel_bill,
                'cancel_vat': cancel_vat,
                'cancel_gross_dis': cancel_gross_dis,
                'total_seller_carrying': total_seller_carrying,
                'total_buyer_carrying': total_buyer_carrying,
            })

            # Update the grand totals
            grand_total_bill += total_bill
            grand_cancel_bill += cancel_bill
            grand_cancel_vat += cancel_vat
            grand_cancel_gross_dis += cancel_gross_dis

        # Calculate payment sums
        collection_amt = payments.filter(collection_mode="1").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        due_collection_amt = payments.filter(collection_mode="2").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        adjust_collection_amt = payments.filter(collection_mode="4").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        refund_amt = payments.filter(collection_mode="3").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0

        grand_vat_tax = total_vat_tax - grand_cancel_vat
        grand_discount = total_gross_dis - grand_cancel_gross_dis

        grand_net_bill = (grand_total_bill + grand_vat_tax + total_buyer_carrying) - (grand_cancel_bill + grand_discount)
        grand_net_bill = round(grand_net_bill, 0)

        grand_net_coll = (collection_amt + due_collection_amt + adjust_collection_amt) - refund_amt
        net_due_amt = grand_net_bill - grand_net_coll
        net_due_amt = round(net_due_amt, 0)

        # Create a context dictionary with the data
        invoice_items.append({
            'inv_id': invoice.inv_id,
            'org_id': invoice.org_id.org_id if invoice.org_id else None,
            'org_name': invoice.org_id.org_name if invoice.org_id else None,
            'branch_id': invoice.branch_id.branch_id if invoice.branch_id else None,
            'branch_name': invoice.branch_id.branch_name if invoice.branch_id else None,
            'supplier_id': invoice.supplier_id.supplier_id if invoice.supplier_id else None,
            'supplier_name': invoice.supplier_id.supplier_name if invoice.supplier_id else None,
            'invoice_date': invoice.invoice_date,
            'customer_name': invoice.customer_name,
            'gender': invoice.gender,
            'mobile_number': invoice.mobile_number,
            # Add other invoice fields as needed
        })

        payments_amt = [{
            'collection_amt_sum': collection_amt,
            'due_collection_amt_sum': due_collection_amt,
            'adjust_collection_amt': adjust_collection_amt,
            'refund_amt_sum': refund_amt,
            'grand_net_bill': grand_net_bill,
            'grand_net_coll': grand_net_coll,
            'net_due_amt': net_due_amt,
        }]

        context = {
            'invoice_items': invoice_items,
            'invoicedtl_data': invoicedtl_items,
            'payments_amt': payments_amt,
        }

        # Return the data as a JSON response
        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# refund collection data view
@login_required()
def getRefundAmountDataAPI(request, inv_id):
    
    try:
        # Retrieve the invoice based on inv_id or return a 404 error if not found
        invoice = get_object_or_404(invoice_list, inv_id=inv_id)

        # Retrieve the related invoicedtl data based on inv_id
        invoicedtl_data = invoicedtl_list.objects.filter(inv_id=inv_id)

        # Retrieve payments related to the invoice
        payments = payment_list.objects.filter(inv_id=invoice)
        # carrying cost buyer wise
        carrying_cost = rent_others_exps.objects.filter(inv_id=invoice)

        # Initialize lists to store invoicedtl data, invoice data, and payments amounts
        invoicedtl_items = []
        invoice_items = []
        payments_amt = {}

        grand_total_bill = 0
        grand_cancel_bill = 0
        grand_cancel_vat = 0
        grand_cancel_gross_dis = 0
        total_vat_tax = 0
        total_gross_dis = 0
        total_seller_carrying = 0
        total_buyer_carrying = 0
        
        for carrying in carrying_cost:
            if carrying.is_seller==True:
                total_seller_carrying += carrying.other_exps_amt
            if carrying.is_buyer==True:
                total_buyer_carrying += carrying.other_exps_amt

        # Create a list of dictionaries containing invoicedtl data
        for item in invoicedtl_data:
            cancel_item_w_dis = (item.item_w_dis / item.qty) * item.is_cancel_qty

            total_bill = (item.sales_rate * item.qty) - item.item_w_dis
            cancel_bill = (item.sales_rate * item.is_cancel_qty) - cancel_item_w_dis
            cancel_vat = (item.gross_vat_tax / item.qty) * item.is_cancel_qty
            cancel_gross_dis = (item.gross_dis / item.qty) * item.is_cancel_qty

            total_vat_tax += item.gross_vat_tax
            total_gross_dis += item.gross_dis

            invoicedtl_items.append({
                'invdtl_id': item.invdtl_id,
                'item_no': item.item_id.item_no,
                'item_name': item.item_id.item_name,
                'item_type': item.item_id.type_id.type_name,
                # 'batch': item.stock_id.item_batch,
                'item_w_dis': item.item_w_dis,
                'gross_dis': item.gross_dis,
                'vat_tax': item.gross_vat_tax,
                'sales_rate': item.sales_rate,
                'qty': item.qty,
                'canncelled_qty': item.is_cancel_qty,
                'cancel_reason': item.cancel_reason,
                'total_bill': total_bill,
                'total_dis': item.gross_dis,
                'cancel_bill': cancel_bill,
                'cancel_vat': cancel_vat,
                'cancel_gross_dis': cancel_gross_dis,
                'total_seller_carrying': total_seller_carrying,
                'total_buyer_carrying': total_buyer_carrying,
            })

            # Update the grand totals
            grand_total_bill += total_bill
            grand_cancel_bill += cancel_bill
            grand_cancel_vat += cancel_vat
            grand_cancel_gross_dis += cancel_gross_dis

        # Calculate payment sums
        collection_amt = payments.filter(collection_mode="1").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        due_collection_amt = payments.filter(collection_mode="2").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        adjust_collection_amt = payments.filter(collection_mode="4").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        refund_amt = payments.filter(collection_mode="3").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0

        grand_vat_tax = total_vat_tax - grand_cancel_vat
        grand_discount = total_gross_dis - grand_cancel_gross_dis

        grand_net_bill = (grand_total_bill + grand_vat_tax + total_buyer_carrying) - (grand_cancel_bill + grand_discount)
        grand_net_bill = round(grand_net_bill, 0)

        grand_net_coll = (collection_amt + due_collection_amt + adjust_collection_amt) - refund_amt
        net_due_amt = grand_net_bill - grand_net_coll
        net_due_amt = round(net_due_amt, 0)

        # + tot_carrying

        # Create a context dictionary with the data
        invoice_items.append({
            'inv_id': invoice.inv_id,
            'org_id': invoice.org_id.org_id if invoice.org_id else None,
            'org_name': invoice.org_id.org_name if invoice.org_id else None,
            'branch_id': invoice.branch_id.branch_id if invoice.branch_id else None,
            'branch_name': invoice.branch_id.branch_name if invoice.branch_id else None,
            'supplier_id': invoice.supplier_id.supplier_id if invoice.supplier_id else None,
            'supplier_name': invoice.supplier_id.supplier_name if invoice.supplier_id else None,
            'invoice_date': invoice.invoice_date,
            'customer_name': invoice.customer_name,
            'gender': invoice.gender,
            'mobile_number': invoice.mobile_number,
            # Add other invoice fields as needed
        })

        payments_amt = [{
            'collection_amt_sum': collection_amt,
            'due_collection_amt_sum': due_collection_amt,
            'adjust_collection_amt': adjust_collection_amt,
            'refund_amt_sum': refund_amt,
            'grand_net_bill': grand_net_bill,
            'grand_net_coll': grand_net_coll,
            'net_due_amt': net_due_amt,
        }]

        context = {
            'invoice_items': invoice_items,
            'invoicedtl_data': invoicedtl_items,
            'payments_amt': payments_amt,
        }

        # Return the data as a JSON response
        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})


    
# save due refund collection
@login_required()
def saveDueCollectionAmountAPI(request):
    resp = {'status': 'failed', 'msg': 'Failed'}
    data = request.POST

    inv_id = data.get('dueRef_searchID')
    org_id = data.get('org_id_due')
    branch_id = data.get('branch_id_due')
    due_amt = int(data.get('total_due_amount'))
    payment_amt = int(data.get('total_payment_amt'))
    collection_mode = int(data.get('pay_Collection_mode'))

    try:
        if due_amt > 0:
            if collection_mode == 3:
                return JsonResponse({'success': False, 'errmsg': 'This Invoice refund not found. Need to Due Collection.'})
        elif due_amt < 0:
            if collection_mode == 2:
                return JsonResponse({'success': False, 'errmsg': 'This Invoice Needs to be refunded. Please Refund This Invoice.'})
        elif due_amt < 0:
            if collection_mode == 4:
                return JsonResponse({'success': False, 'errmsg': 'This Invoice Needs to be refunded. Please Refund This Invoice.'})
            
        elif due_amt == 0:
            return JsonResponse({'success': False, 'errmsg': 'This Invoice Has No Due ...'})

        with transaction.atomic():

            invoice = invoice_list.objects.get(inv_id=inv_id)

            given_amt = data['given_amt'] if data['given_amt'].strip() else 0
            change_amt = data['change_amt'] if data['change_amt'].strip() else 0

            org_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)

            # Create and save the payment record
            due_ref_payment = payment_list(
                inv_id=invoice,
                pay_mode=data['pay_mode'],
                collection_mode=data['pay_Collection_mode'],
                pay_amt=payment_amt,
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
            due_ref_payment.save()

            if due_amt > 0 and collection_mode == 2:
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=org_instance,
                    branch_id=branch_instance,
                    defaults={
                        'on_hand_cash': 0,  # Initialize to 0 if a new record is created
                    }
                )

                # Update the on_hand_cash by adding due_amt
                cashOnHands.on_hand_cash = F('on_hand_cash') + payment_amt
                cashOnHands.save()
                # Refresh from the database to get the updated value of on_hand_cash
                cashOnHands.refresh_from_db()

            resp['status'] = 'success'
            resp['invoice_id'] = invoice.inv_id

            return JsonResponse({'success': True, 'msg': 'Successful!'})
    except Exception as e:
        print("Unexpected error:", sys.exc_info()[0])
        resp['errmsg'] = str(e)
        return JsonResponse(resp)
    


@login_required()
def saveRefundAmountAPI(request):
    resp = {'status': 'failed', 'msg': 'Failed'}
    data = request.POST

    inv_id = data.get('refAmt_searchID')
    org_id = data.get('org_id')
    branch_id = data.get('branch_id')
    refund_amt = int(data.get('total_due_amount_ref'))
    payment_amt = int(data.get('total_payment_amt_ref'))
    collection_mode = int(data.get('pay_Collection_mode_ref'))

    try:
        if refund_amt > 0:
            if collection_mode == 3:
                return JsonResponse({'success': False, 'errmsg': 'This Invoice refund not found. Need to Due Collection.'})
        elif refund_amt < 0:
            if collection_mode == 2:
                return JsonResponse({'success': False, 'errmsg': 'Please Select Collection Mode "Refund" ...'})
        elif refund_amt == 0:
            return JsonResponse({'success': False, 'errmsg': 'This Invoice Has No Due ...'})

        with transaction.atomic():

            invoice = invoice_list.objects.get(inv_id=inv_id)

            given_amt = data['given_amt_ref'] if data['given_amt_ref'].strip() else 0
            change_amt = data['change_amt_ref'] if data['change_amt_ref'].strip() else 0

            org_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)

            # Create and save the payment record
            due_ref_payment = payment_list(
                inv_id=invoice,
                pay_mode=data['pay_mode_ref'],
                collection_mode=data['pay_Collection_mode_ref'],
                pay_amt=payment_amt,
                given_amt=given_amt,
                change_amt=change_amt,
                card_info=data['card_info_ref'],
                pay_mob_number=data['pay_mob_number_ref'],
                pay_reference=data['pay_reference_ref'],
                bank_name=data['bank_name_ref'],
                remarks=data['remarks_ref'],
                ss_creator=request.user,
                ss_modifier=request.user,
            )
            due_ref_payment.save()

            if refund_amt < 0 and collection_mode == 3:
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=org_instance,
                    branch_id=branch_instance,
                    defaults={
                        'on_hand_cash': 0,  # Initialize to 0 if a new record is created
                    }
                )

                # Update the on_hand_cash by subs payment_amt
                cashOnHands.on_hand_cash = F('on_hand_cash') - payment_amt
                cashOnHands.save()
                # Refresh from the database to get the updated value of on_hand_cash
                cashOnHands.refresh_from_db()

            resp['status'] = 'success'
            resp['invoice_id'] = invoice.inv_id

            return JsonResponse({'success': True, 'msg': 'Successful!'})
    except Exception as e:
        print("Unexpected error:", sys.exc_info()[0])
        resp['errmsg'] = str(e)
        return JsonResponse(resp)