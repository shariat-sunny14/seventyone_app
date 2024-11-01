
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
from bank_statement.models import cash_on_hands, daily_bank_statement
from local_purchase.models import local_purchase, local_purchasedtl
from local_purchase_return.models import lp_return_details
from manual_return_receive.models import manual_return_receive, manual_return_receivedtl
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
    grand_mb_total_cost = 0
    grand_b_total_cost = 0
    total_daily_deposit = 0
    deposit_main_branch = 0
    dep_rec_sub_branch = 0
    total_cash_on_hand = 0
    grand_mobile_bank_coll = 0
    grand_total_bank_coll = 0
    grand_total_amt = 0
    grand_ret_total_amt = 0
    grand_mrr_total_amt = 0

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
            mobile_bank_payments = payment_list.objects.filter( pay_date__range=(start_from, end_from), inv_id__org_id=org_id, inv_id__branch_id=branch_id, pay_mode__in=["5", "6", "7", "8"]).all()
            bank_payments = payment_list.objects.filter( pay_date__range=(start_from, end_from), inv_id__org_id=org_id, inv_id__branch_id=branch_id, pay_mode__in=["2", "3", "4"]).all()
            other_rent_exp = rent_others_exps.objects.filter(other_exps_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id).all()
            carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True, org_id=org_id, branch_id=branch_id).all()
            invoice_details = invoicedtl_list.objects.filter(inv_id__org_id=org_id, inv_id__branch_id=branch_id).all()
            bank_deposits = daily_bank_statement.objects.filter(deposit_date__range=(start_from, end_from), is_bank_statement=True, org_id=org_id, branch_id=branch_id).all()
            daily_cash_on_hand = cash_on_hands.objects.filter(org_id=org_id, branch_id=branch_id)
            local_purchases = local_purchase.objects.filter(transaction_date__range=(start_from, end_from), is_approved=True, is_cash=True, id_org=org_id, branch_id=branch_id)
            local_purchasedtls = local_purchasedtl.objects.filter(lp_rec_date__range=(start_from, end_from)).select_related('lp_id').all()
            lp_returndtls = lp_return_details.objects.filter(returned_date__range=(start_from, end_from)).select_related('lp_id').all()
            manual_return_rec = manual_return_receive.objects.filter(transaction_date__range=(start_from, end_from), is_approved=True, is_cash=True, id_org=org_id, branch_id=branch_id)
            manu_return_recdtls = manual_return_receivedtl.objects.filter(manu_ret_rec_date__range=(start_from, end_from)).select_related('manu_ret_rec_id').all()
            submit_main_branch = daily_bank_statement.objects.filter(deposit_date__range=(start_from, end_from), is_branch_deposit=True, org_id=org_id, branch_id=branch_id).all()
            deposit_rec_sub_branch = daily_bank_statement.objects.filter(deposit_date__range=(start_from, end_from), is_branch_deposit_receive=True, org_id=org_id, branch_id=branch_id).all()
            
            # manual return receive 
            for mret_rec in manual_return_rec:
                # Filter manu return recdtls
                manu_ret_rec_details = manu_return_recdtls.filter(manu_ret_rec_id=mret_rec)

                for manurrdtl in manu_ret_rec_details:
                    # Extract relevant attributes
                    mrr_qty = manurrdtl.manu_ret_rec_qty or 0  # Default to 0 if None
                    mrr_price = manurrdtl.unit_price or 0
                    mrr_discount = manurrdtl.dis_percentage or 0

                    # Calculate total amount, discount, and final amount
                    mrr_totalamt = mrr_qty * mrr_price
                    total_mrr_dis_per = mrr_discount / 100
                    total_mrr_dis_amt = mrr_totalamt * total_mrr_dis_per

                    # Accumulate the final amount
                    grand_mrr_total_amt += mrr_totalamt - total_mrr_dis_amt

            for lpdata in local_purchases:
                # Filter purchase details and return details by local purchase ID
                lp_details = local_purchasedtls.filter(lp_id=lpdata)
                lp_return_dtls = lp_returndtls.filter(lp_id=lpdata)

                for detail in lp_details:
                    # Extract relevant attributes
                    lp_qty = detail.lp_rec_qty or 0  # Default to 0 if None
                    lp_price = detail.unit_price or 0
                    lp_discount = detail.dis_percentage or 0

                    # Calculate total amount, discount, and final amount
                    lp_totalamt = lp_qty * lp_price
                    total_lp_dis_per = lp_discount / 100
                    total_dis_amt = lp_totalamt * total_lp_dis_per

                    # Accumulate the final amount
                    grand_total_amt += lp_totalamt - total_dis_amt

                for returndtls in lp_return_dtls:
                    # Fetch the relevant `local_purchasedtl` record for the returned item
                    related_detail = local_purchasedtl.objects.filter(lp_id=returndtls.lp_id, item_id=returndtls.item_id).first()

                    if related_detail:
                        # Extract attributes from the related detail instance
                        lp_ret_qty = returndtls.lp_return_qty or 0
                        lp_ret_can_qty = returndtls.is_cancel_qty or 0
                        lp_ret_price = related_detail.unit_price or 0
                        lp_ret_discount = related_detail.dis_percentage or 0

                        # Calculate total amount, discount, and final amount for return
                        lp_ret_totalamt = (lp_ret_qty - lp_ret_can_qty) * lp_ret_price
                        total_lpret_dis_per = lp_ret_discount / 100
                        total_ret_dis_amt = lp_ret_totalamt * total_lpret_dis_per

                        # Accumulate the return amount
                        grand_ret_total_amt += lp_ret_totalamt - total_ret_dis_amt

            # Sum the diposit rec from sub branch over the date range
            dep_rec_sub_branch = deposit_rec_sub_branch.aggregate(
                total_amount=Sum('deposits_amt')
            )['total_amount'] or 0  # Return 0 if no deposits are found

            # Sum the diposit of the main branch over the date range
            deposit_main_branch = submit_main_branch.aggregate(
                total_amount=Sum('deposits_amt')
            )['total_amount'] or 0  # Return 0 if no deposits are found

            # Sum the deposits_amt over the date range
            total_daily_deposit = bank_deposits.aggregate(
                total_amount=Sum('deposits_amt')
            )['total_amount'] or 0  # Return 0 if no deposits are found

            # Calculate total cash on hand
            total_cash_on_hand = sum(hands.on_hand_cash for hands in daily_cash_on_hand)

            # Calculate carrying cost from buyer per inv_id
            buyer_total_cost = carrying_cost_buyer.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                total_cost=Sum(F('other_exps_amt'), output_field=FloatField())
            )

            # Calculate carrying cost from buyer per inv_id, using filtered payments
            mobile_bank_carring_cost = carrying_cost_buyer.filter(inv_id__in=mobile_bank_payments.values_list('inv_id', flat=True)).values('inv_id').annotate(mb_total_cost=Sum(F('other_exps_amt'), output_field=FloatField()))

            # Calculate carrying cost from buyer per inv_id, using filtered payments
            bank_carring_cost = carrying_cost_buyer.filter(inv_id__in=bank_payments.values_list('inv_id', flat=True)).values('inv_id').annotate(b_total_cost=Sum(F('other_exps_amt'), output_field=FloatField()))

            # Check if invoice_details exist
            if invoice_details.exists():
                # Calculate total sales per inv_id
                sales_totals = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    total_sales=Sum(F('sales_rate') * F('qty'), output_field=FloatField())
                )

                item_w_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    item_disc=Sum(((F('item_w_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
                )

                gross_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    gross_disc=Sum(((F('gross_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
                )

                item_w_gross_vat_tax = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    total_vat_tax=Sum(((F('gross_vat_tax') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
                )

                cancel_amt = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    total_cancel_amt=Sum((F('sales_rate') * F('is_cancel_qty')), output_field=FloatField())
                )
            else:
                # Set all totals to 0.0 if no invoice details are found
                sales_totals = [{'total_sales': 0}]
                item_w_discount = [{'item_disc': 0}]
                gross_discount = [{'gross_disc': 0}]
                item_w_gross_vat_tax = [{'total_vat_tax': 0}]
                cancel_amt = [{'total_cancel_amt': 0}]

            # Create a dictionary to store collections for each inv_id
            collections_by_inv_id = defaultdict(lambda: {
                'total_collection_amt': 0.0,
                'total_due_collection_amt': 0.0,
                'total_refund_collection_amt': 0.0,
                'total_adjust_amt': 0.0,
                'total_sales': 0.0,
                'total_cost': 0.0,
                'mb_total_cost': 0.0,
                'b_total_cost': 0.0,
                'item_disc': 0.0,
                'gross_disc': 0.0,
                'total_vat_tax': 0.0,
                'total_cancel_amt': 0.0,
                'total_net_bill': 0.0,
                'total_bkash_coll_amt': 0.0,
                'total_nagad_coll_amt': 0.0,
                'total_upay_coll_amt': 0.0,
                'total_ucash_coll_amt': 0.0,
                'total_check_coll_amt': 0.0,
                'total_debit_coll_amt': 0.0,
                'total_credit_coll_amt': 0.0,
            })

            # other rent or expence
            for otherExp in other_rent_exp:
                other_exp_amt = otherExp.other_exps_amt
                total_other_exp_amt += other_exp_amt

            # Define a mapping of pay_mode to collection keys
            pay_mode_mobile_bank_key = {
                "5": 'total_bkash_coll_amt',
                "6": 'total_nagad_coll_amt',
                "7": 'total_upay_coll_amt',
                "8": 'total_ucash_coll_amt',
            }

            pay_mode_bank_key = {
                "2": 'total_check_coll_amt',
                "3": 'total_debit_coll_amt',
                "4": 'total_credit_coll_amt',
            }

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

                # =========================== mobile bank wise collections =====================
                # mobile bank wise collections
                mobile_bank_key = pay_mode_mobile_bank_key.get(paymentData.pay_mode)
                if mobile_bank_key:
                    collections_by_inv_id[paymentData.inv_id][mobile_bank_key] += pay_amt

                # =========================== bank wise collections =====================
                # bank wise collections
                bank_key = pay_mode_bank_key.get(paymentData.pay_mode)
                if bank_key:
                    collections_by_inv_id[paymentData.inv_id][bank_key] += pay_amt

            for inv_id, collections in collections_by_inv_id.items():
                # Get total sales for this inv_id from the annotated values
                try:
                    sales_total_entry = sales_totals.get(inv_id=inv_id)
                    total_sales = sales_total_entry['total_sales'] if sales_total_entry else 0
                    collections['total_sales'] = total_sales
                    grandtotal_sales += total_sales
                except ObjectDoesNotExist:
                    total_sales = 0
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

                ############ mobile bank carring cost
                try:
                    mb_cost_entry = mobile_bank_carring_cost.get(inv_id=inv_id)
                    mb_total_cost = mb_cost_entry['mb_total_cost'] if mb_cost_entry else 0
                    collections['mb_total_cost'] = mb_total_cost
                    grand_mb_total_cost += mb_total_cost
                except ObjectDoesNotExist:
                    mb_total_cost = 0
                    collections['mb_total_cost'] = mb_total_cost
                    grand_mb_total_cost += mb_total_cost

                
                ############ bank carring cost
                try:
                    b_cost_entry = bank_carring_cost.get(inv_id=inv_id)
                    b_total_cost = b_cost_entry['b_total_cost'] if b_cost_entry else 0
                    collections['b_total_cost'] = b_total_cost
                    grand_b_total_cost += b_total_cost
                except ObjectDoesNotExist:
                    b_total_cost = 0
                    collections['b_total_cost'] = b_total_cost
                    grand_b_total_cost += b_total_cost
                
                # item wise discount
                try:
                    item_disc = item_w_discount.get(inv_id=inv_id)['item_disc'] if item_w_discount else 0
                    collections['item_disc'] = item_disc
                    item_disc = round(item_disc, 2)
                except ObjectDoesNotExist:
                    item_disc = 0
                    collections['item_disc'] = item_disc
                    item_disc = round(item_disc, 2)

                # gross discount
                try:
                    gross_disc = gross_discount.get(inv_id=inv_id)['gross_disc'] if gross_discount else 0
                    collections['gross_disc'] = gross_disc
                    gross_disc = round(gross_disc, 2)
                except ObjectDoesNotExist:
                    gross_disc = 0
                    collections['gross_disc'] = gross_disc
                    gross_disc = round(gross_disc, 2)

                # total discount
                total_discount = collections['item_disc'] + collections['gross_disc']
                total_discount = round(total_discount, 2)
                # total discount sun
                grand_total_discount += total_discount
                grand_total_discount = round(grand_total_discount, 2)

                # total vat tax
                try:
                    total_vat_tax = item_w_gross_vat_tax.get(inv_id=inv_id)['total_vat_tax'] if item_w_gross_vat_tax else 0
                    collections['total_vat_tax'] = total_vat_tax
                    total_vat_tax = round(total_vat_tax, 2)
                    # grand total vat tax
                    grand_total_vat_tax += total_vat_tax
                    grand_total_vat_tax = round(grand_total_vat_tax, 2)
                except ObjectDoesNotExist:
                    total_vat_tax = 0
                    collections['total_vat_tax'] = total_vat_tax
                    total_vat_tax = round(total_vat_tax, 2)
                    # grand total vat tax
                    grand_total_vat_tax += total_vat_tax
                    grand_total_vat_tax = round(grand_total_vat_tax, 2)

                # total cancel amount
                try:
                    total_cancel_amt = cancel_amt.get(inv_id=inv_id)['total_cancel_amt'] if cancel_amt else 0
                    collections['total_cancel_amt'] = total_cancel_amt
                    total_cancel_amt = round(total_cancel_amt, 2)
                    # grand total cancel amount
                    grand_total_cancel_amt += total_cancel_amt
                    grand_total_cancel_amt = round(grand_total_cancel_amt, 2)
                except ObjectDoesNotExist:
                    total_cancel_amt = 0
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

                ################# mobile bank collection #######################
                total_mobile_bank_coll = collections['total_bkash_coll_amt'] + collections['total_nagad_coll_amt'] + collections['total_upay_coll_amt'] + collections['total_ucash_coll_amt'] - collections['mb_total_cost']
                grand_mobile_bank_coll += total_mobile_bank_coll
                grand_mobile_bank_coll = round(grand_mobile_bank_coll, 2)

                ################# bank collection #######################
                total_bank_coll = collections['total_check_coll_amt'] + collections['total_debit_coll_amt'] + collections['total_credit_coll_amt']
                grand_total_bank_coll += total_bank_coll
                grand_total_bank_coll = round(grand_total_bank_coll, 2)

                ########################################
                grand_collection = collections['total_collection_amt'] + collections['total_due_collection_amt']
                grand_collection = round(grand_collection, 2)
                # total net collection
                total_net_collection = ((collections['total_collection_amt'] + collections['total_due_collection_amt']) - (collections['total_refund_collection_amt']))
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


                grand_total_collection = (grand_total_net_collection + grand_ret_total_amt + dep_rec_sub_branch) - (total_other_exp_amt + grand_total_bank_coll + grand_total_amt + grand_mrr_total_amt)

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
                'total_daily_deposit': total_daily_deposit,
                'deposit_main_branch': deposit_main_branch,
                'dep_rec_sub_branch': dep_rec_sub_branch,
                'total_cash_on_hand': total_cash_on_hand,
                'grand_mobile_bank_coll': grand_mobile_bank_coll,
                'grand_total_bank_coll': grand_total_bank_coll,
                'grand_total_amt': grand_total_amt,
                'grand_ret_total_amt': grand_ret_total_amt,
                'grand_mrr_total_amt': grand_mrr_total_amt,
            }
    
            return JsonResponse(data)
        
        except Exception as e:
            # Log the exception
            print("An error occurred:", e)
            return JsonResponse({'error': str(e)}, status=500)
            # return JsonResponse({'error': 'An error occurred while processing the request'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
