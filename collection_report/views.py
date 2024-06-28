
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum
from collections import defaultdict
from django.db.models import FloatField
from decimal import Decimal
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def collectionsReportManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(
            is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    context = {
        'org_list': org_list,
    }

    return render(request, 'sales_coll_report/collection_report.html', context)


@login_required()
def collectionsReportAPI(request):
    
    start_from = None
    end_from = None

    # Define context here
    combined_data = []

    grand_total_net_collection = 0
    total_collection = 0
    total_due_collection = 0
    total_grand_collection = 0
    total_refund_collection = 0
    total_adjust_collection = 0
    grandtotal_sales = 0
    grand_total_discount = 0
    grand_total_vat_tax = 0
    grand_total_cancel_amt = 0
    grand_total_net_bill = 0
    total_other_exp_amt = 0
    grand_total_collection = 0
    grandtotal_cost = 0

    if request.method == "POST":
        try:
            start_from = request.POST.get('start_from')
            end_from = request.POST.get('end_from')
            org_id = request.POST.get('org_id')
            branch_id = request.POST.get('branch_id')

            # Parse the dates from the request POST data
            start_from = datetime.strptime(start_from, '%Y-%m-%d').date()
            end_from = datetime.strptime(end_from, '%Y-%m-%d').date()

            # Query data from your models
            payments = payment_list.objects.filter(pay_date__range=(start_from, end_from), inv_id__org_id=org_id, inv_id__branch_id=branch_id).all()
            other_rent_exp = rent_others_exps.objects.filter(other_exps_date__range=(start_from, end_from)).all()
            carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True).all()
            invoice_details = invoicedtl_list.objects.all()

            # Calculate carrying cost from buyer per inv_id
            buyer_total_cost = carrying_cost_buyer.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                total_cost=Sum(F('other_exps_amt'), output_field=FloatField())
            )

            # Calculate total sales per inv_id
            sales_totals = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                total_sales=Sum(F('sales_rate') * F('qty'), output_field=FloatField())
            )

            item_w_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                item_disc=Sum(((F('item_w_dis') / F('qty')) *
                            ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
            )

            gross_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                gross_disc=Sum(((F('gross_dis') / F('qty')) *
                            ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
            )

            item_w_gross_vat_tax = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                total_vat_tax=Sum(((F('gross_vat_tax') / F('qty')) *
                                ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
            )

            cancel_amt = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                total_cancel_amt=Sum(
                    (F('sales_rate') * F('is_cancel_qty')), output_field=FloatField())
            )

            # Create a dictionary to store collections for each inv_id
            collections_by_inv_id = defaultdict(lambda: {
                'total_collection_amt': 0.0,
                'total_due_collection_amt': 0.0,
                'total_refund_collection_amt': 0.0,
                'total_adjust_amt': 0.0,
                'total_sales': 0.0,
                'total_cost': 0.0,
                'item_disc': 0.0,
                'gross_disc': 0.0,
                'total_vat_tax': 0.0,
                'total_cancel_amt': 0.0,
                'total_net_bill': 0.0,
            })

            # other rent or expence
            for otherExp in other_rent_exp:
                other_exp_amt = otherExp.other_exps_amt
                total_other_exp_amt += other_exp_amt


            for paymentData in payments:
                # Convert pay_amt to a float
                pay_amt = float(paymentData.pay_amt)
                # collection
                if paymentData.collection_mode == "1":
                    collections_by_inv_id[paymentData.inv_id]['total_collection_amt'] += pay_amt
                # due collection
                elif paymentData.collection_mode == "2":
                    collections_by_inv_id[paymentData.inv_id]['total_due_collection_amt'] += pay_amt

                # Refund collection
                elif paymentData.collection_mode == "3":
                    collections_by_inv_id[paymentData.inv_id]['total_refund_collection_amt'] += pay_amt
                
                # Adjust collection
                elif paymentData.collection_mode == "4":
                    collections_by_inv_id[paymentData.inv_id]['total_adjust_amt'] += pay_amt

            for inv_id, collections in collections_by_inv_id.items():
                # Get total sales for this inv_id from the annotated values
                sales_total_entry = sales_totals.get(inv_id=inv_id)
                total_sales = sales_total_entry['total_sales'] if sales_total_entry else 0
                collections['total_sales'] = total_sales
                grandtotal_sales += total_sales

                try:
                    cost_entry = buyer_total_cost.get(inv_id=inv_id)
                    total_cost = cost_entry['total_cost'] if cost_entry else 0
                    collections['total_cost'] = total_cost
                    grandtotal_cost += total_cost
                except ObjectDoesNotExist:
                    total_cost = 0
                    collections['total_cost'] = total_cost
                    grandtotal_cost += total_cost
                
                # item wise discount
                item_disc = item_w_discount.get(inv_id=inv_id)['item_disc']
                collections['item_disc'] = item_disc
                item_disc = round(item_disc, 2)
                # gross discount
                gross_disc = gross_discount.get(inv_id=inv_id)['gross_disc']
                collections['gross_disc'] = gross_disc
                gross_disc = round(gross_disc, 2)
                # total discount
                total_discount = collections['item_disc'] + collections['gross_disc']
                total_discount = round(total_discount, 2)
                # total discount sun
                grand_total_discount += total_discount
                grand_total_discount = round(grand_total_discount, 2)

                # total vat tax
                total_vat_tax = item_w_gross_vat_tax.get(inv_id=inv_id)[
                    'total_vat_tax']
                collections['total_vat_tax'] = total_vat_tax
                total_vat_tax = round(total_vat_tax, 2)
                # grand total vat tax
                grand_total_vat_tax += total_vat_tax
                grand_total_vat_tax = round(grand_total_vat_tax, 2)

                # total cancel amount
                total_cancel_amt = cancel_amt.get(inv_id=inv_id)['total_cancel_amt']
                collections['total_cancel_amt'] = total_cancel_amt
                total_cancel_amt = round(total_cancel_amt, 2)
                # grand total cancel amount
                grand_total_cancel_amt += total_cancel_amt
                grand_total_cancel_amt = round(grand_total_cancel_amt, 2)

                # total net bill
                total_net_bill = ((collections['total_sales'] + collections['total_vat_tax'] + collections['total_cost']) - (collections['item_disc'] + collections['gross_disc']) - collections['total_cancel_amt'])
                total_net_bill = round(total_net_bill, 2)
                # grand total_net_bill
                grand_total_net_bill += total_net_bill
                grand_total_net_bill = round(grand_total_net_bill, 2)

                ########################################
                grand_collection = collections['total_collection_amt'] + collections['total_due_collection_amt']
                grand_collection = round(grand_collection, 2)
                # total net collection
                total_net_collection = ((collections['total_collection_amt'] + collections['total_due_collection_amt']) - collections['total_refund_collection_amt'])
                total_net_collection = round(total_net_collection, 2)

                # total collection amt
                collection = collections['total_collection_amt']
                collection = round(collection, 2)
                total_collection += collection
                total_collection = round(total_collection, 2)

                # total due collection amt
                due_collection = collections['total_due_collection_amt']
                due_collection = round(due_collection, 2)
                total_due_collection += due_collection
                total_due_collection = round(total_due_collection, 2)

                # total collection amt + total due collection amt
                total_grand_collection += grand_collection
                total_grand_collection = round(total_grand_collection, 2)

                # total refund collection
                refund_collection = collections['total_refund_collection_amt']
                refund_collection = round(refund_collection, 2)
                total_refund_collection += refund_collection
                total_refund_collection = round(total_refund_collection, 2)


                # total Adjust collection
                adjust_collection = collections['total_adjust_amt']
                adjust_collection = round(adjust_collection, 2)
                total_adjust_collection += adjust_collection
                total_adjust_collection = round(total_adjust_collection, 2)

                # grand total net collection
                grand_total_net_collection += total_net_collection
                grand_total_net_collection = round(grand_total_net_collection, 2)


                grand_total_collection = grand_total_net_collection - total_other_exp_amt

                combined_data.append({
                    'inv_id': inv_id.inv_id,  # Assuming inv_id is the primary key
                    'invoice_date': inv_id.invoice_date.strftime('%Y-%m-%d'),
                    'customer_name': inv_id.customer_name,
                    'address': inv_id.address,
                    'mobile_number': inv_id.mobile_number,
                    # Include other relevant fields similarly
                    'total_sales': total_sales,
                    'total_cost': total_cost,
                    'total_discount': total_discount,
                    'total_vat_tax': total_vat_tax,
                    'total_cancel_amt': total_cancel_amt,
                    'total_net_bill': total_net_bill,
                    'total_collection_amt': collections['total_collection_amt'],
                    'total_due_collection_amt': collections['total_due_collection_amt'],
                    'total_refund_collection_amt': collections['total_refund_collection_amt'],
                    'total_adjust_amt': collections['total_adjust_amt'],
                    'grand_collection': grand_collection,
                    'total_net_collection': total_net_collection,
                })

            data = {
                'combined_data': combined_data,
                'total_collection': total_collection,
                'total_due_collection': total_due_collection,
                'total_grand_collection': total_grand_collection,
                'total_refund_collection': total_refund_collection,
                'total_adjust_collection': total_adjust_collection,
                'grand_total_net_collection': grand_total_net_collection,
                'grandtotal_sales': grandtotal_sales,
                'grand_total_discount': grand_total_discount,
                'grand_total_vat_tax': grand_total_vat_tax,
                'grand_total_cancel_amt': grand_total_cancel_amt,
                'grand_total_net_bill': grand_total_net_bill,
                'total_other_exp_amt': total_other_exp_amt,
                'grand_total_collection': grand_total_collection,
                'grandtotal_cost': grandtotal_cost,
            }
    
            return JsonResponse(data)
        
        except Exception as e:
            # Log the exception
            print("An error occurred:", e)
            return JsonResponse({'error': str(e)}, status=500)
            # return JsonResponse({'error': 'An error occurred while processing the request'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
