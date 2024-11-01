import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField
from django.contrib import messages
from item_setup.models import items
from store_setup.models import store
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from stock_list.stock_qty import get_available_qty
from registrations.models import in_registrations
from local_purchase.models import local_purchase, local_purchasedtl
from local_purchase_return.models import lp_return_details
from bank_statement.models import cash_on_hands
from supplier_setup.models import suppliers
from stock_list.models import in_stock, stock_lists
from item_pos.models import invoicedtl_list
from opening_stock.models import opening_stockdtl
from others_setup.models import item_type
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def lPReturnListManagerAPI(request):
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
    return render(request, 'local_purchase_return/local_purchase_return_list.html', context)


@login_required()
def getLocalPurchaseReturnListAPI(request):
    pol_option = request.GET.get('pol_option')
    org_id_wise_filter = request.GET.get('filter_org', '')
    branch_id_wise_filter = request.GET.get('filter_branch', '')
    po_start = request.GET.get('op_start')
    po_end = request.GET.get('op_end')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(id_org=org_id_wise_filter)
    
    if branch_id_wise_filter:
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)

    # Add is_active filter condition based on typeoption
    if pol_option == 'true':
        filter_kwargs &= Q(is_returned=True)
    elif pol_option == 'false':
        filter_kwargs &= Q(is_returned=False)

    # Add date range filter conditions with validation
    try:
        if po_start:
            start_date = datetime.strptime(po_start, '%Y-%m-%d')
            filter_kwargs &= Q(transaction_date__gte=start_date)
        if po_end:
            end_date = datetime.strptime(po_end, '%Y-%m-%d')
            filter_kwargs &= Q(transaction_date__lte=end_date)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid date format: {e}'}, status=400)

    # Query the data
    lp_data = local_purchase.objects.filter(is_approved=True).filter(filter_kwargs)

    # Prepare response data
    data = []
    for lp_list in lp_data:
        org_name = lp_list.id_org.org_name if lp_list.id_org else None
        branch_name = lp_list.branch_id.branch_name if lp_list.branch_id else None
        store_name = lp_list.store_id.store_name if lp_list.store_id else None
        is_returned_by_first = lp_list.is_returned_by.first_name if lp_list.is_returned_by else ""
        is_returned_by_last = lp_list.is_returned_by.last_name if lp_list.is_returned_by else ""
        returned_date = lp_list.returned_date if lp_list.returned_date is not None else ""
        data.append({
            'lp_id': lp_list.lp_id,
            'lp_no': lp_list.lp_no,
            'clients_name': lp_list.reg_id.full_name if lp_list.reg_id else lp_list.cus_clients_name,
            'mobile_number': lp_list.reg_id.mobile_number if lp_list.reg_id else lp_list.cus_mobile_number,
            'transaction_date': lp_list.transaction_date,
            'returned_date': returned_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'invoice_no': lp_list.invoice_no,
            'invoice_date': lp_list.invoice_date,
            'is_returned': lp_list.is_returned,
            'is_returned_by_first': is_returned_by_first,
            'is_returned_by_last': is_returned_by_last,
        })

    return JsonResponse({'data': data})


# Local Purchase Return
@login_required()
def localPurchaseReturnManagerAPI(request, lp_id=None):
    # Fetch active items and main stores ordered by store_no
    items_data = items.objects.filter(is_active=True)
    stores = store.objects.filter(is_main_store=1).order_by('store_no')

    ops_data = local_purchase.objects.filter(pk=lp_id).first() if lp_id else None
    ops_details = local_purchasedtl.objects.filter(lp_id=ops_data) if ops_data else []

    # Exclude the store of the current purchase if it exists
    if ops_data:
        stores = stores.exclude(store_id=ops_data.store_id.store_id)

    item_with_ops_dtls = []
    grand_total_qty = grand_po_rec_qty = grand_po_return_qty = grand_is_canceled_qty = 0

    for item in items_data:
        store_instance = ops_data.store_id if ops_data else None
        lp_id_instance = ops_data.lp_id if ops_data else None

        # Fetch PO received and return quantities
        po_rec_qty = (
            local_purchasedtl.objects.filter(item_id=item, lp_id=lp_id_instance)
            .aggregate(total=Sum(F('lp_rec_qty'), output_field=FloatField()))['total'] or 0
        )
        po_return_qty = (
            lp_return_details.objects.filter(item_id=item, lp_id=lp_id_instance)
            .aggregate(total=Sum(F('lp_return_qty'), output_field=FloatField()))['total'] or 0
        )

        is_canceled_qty = (
            lp_return_details.objects.filter(item_id=item, lp_id=lp_id_instance)
            .aggregate(total=Sum(F('is_cancel_qty'), output_field=FloatField()))['total'] or 0
        )

        # Aggregate totals
        grand_po_rec_qty += po_rec_qty
        grand_po_return_qty += po_return_qty
        grand_is_canceled_qty += is_canceled_qty

        # Fetch available quantity from helper function
        available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id) if store_instance else 0
        grand_total_qty += available_qty

        # Fetch relevant order details for the item
        order_detail = next((od for od in ops_details if od.item_id == item), None)

        if order_detail:
            item_with_ops_dtls.append({
                'grandQty': available_qty,
                'ops_dtls': order_detail,
                'totalPoRecQty': po_rec_qty,
                'totalIsCanceledQty': is_canceled_qty,
                'totalPoReturnQty': po_return_qty,
                'order_qty': order_detail.lp_rec_qty,
                'unit_price': order_detail.unit_price,
            })

    context = {
        'item_with_opsDtls': item_with_ops_dtls,
        'store_data': stores,
        'ops_Data': ops_data,
        'total_grandQty': grand_total_qty,
    }
    return render(request, 'local_purchase_return/local_purchase_return.html', context)



@login_required()
def saveLocalpurchaseReturnedManagerAPI(request):
    if request.method == 'POST':
        try:
            # Extract data from request
            lp_id = request.POST.get('lp_id')
            current_store_id = request.POST.get('current_store')
            returned_date = request.POST.get('returned_date')
            is_returned = request.POST.get('is_returned')
            is_returned_by = request.POST.get('is_returned_by')
            returned_remarks = request.POST.get('returned_remarks')
            org_id = request.POST.get('org')
            branch_id = request.POST.get('branchs')

            item_ids = request.POST.getlist('item_id[]')
            return_qtys = request.POST.getlist('return_qty[]')
            is_cancel_qtys = request.POST.getlist('is_cancel_qty[]')
            item_batchs = request.POST.getlist('item_batchs[]')
            is_returned_inds = request.POST.getlist('is_returned_ind[]')
            returned_date_ind = request.POST.get('returned_date_ind')

            # Debug: Print IDs to verify correctness
            print(f"lp_id: {lp_id}, current_store_id: {current_store_id}")

            # Start a database transaction
            with transaction.atomic():
                # Validate and get user instance
                user_instance = None
                if is_returned_by:
                    user_instance = User.objects.filter(user_id=is_returned_by).first()
                    if not user_instance:
                        return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)

                # Retrieve local purchase and store instances
                lp_instance = local_purchase.objects.filter(lp_id=lp_id).first()
                store_instance = store.objects.filter(store_id=current_store_id).first()
                org_instance = organizationlst.objects.filter(org_id=org_id).first()
                branch_instance = branchslist.objects.filter(branch_id=branch_id).first()

                if not lp_instance:
                    return JsonResponse({'errmsg': f'Local Purchase with ID {lp_id} not found.'}, status=404)
                if not store_instance:
                    return JsonResponse({'errmsg': f'Store with ID {current_store_id} not found.'}, status=404)

                # Fetch all related purchase details in one query
                lp_details = local_purchasedtl.objects.filter(lp_id=lp_id)

                # Loop through items and save return details
                for item_id, return_qty, is_cancel_qty, is_returned_ind, item_batch in zip(item_ids, return_qtys, is_cancel_qtys, is_returned_inds, item_batchs):
                    # Retrieve item instance
                    item_instance = items.objects.filter(item_id=item_id).first()
                    if not item_instance:
                        return JsonResponse({'errmsg': f'Item with ID {item_id} not found.'}, status=404)
                    
                    # Extract unit price and discount percentage from the purchase details
                    for lpdtls in lp_details:
                        unit_price = lpdtls.unit_price
                        dis_perc = lpdtls.dis_percentage

                    # Save local purchase return details
                    lp_return_dtl = lp_return_details(
                        lp_id=lp_instance,
                        store_id=store_instance,
                        item_id=item_instance,
                        lp_return_qty=float(return_qty) if float(return_qty) > 0 else 0,
                        is_cancel_qty=float(is_cancel_qty) if float(is_cancel_qty) > 0 else 0,
                        item_batch=item_batch,
                        is_returned=is_returned_ind,
                        returned_date=returned_date_ind,
                        returned_remarks=returned_remarks,
                        is_returned_by=user_instance,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )
                    lp_return_dtl.save()

                    # Save stock data
                    stock_data = stock_lists(
                        lp_id=lp_instance,
                        lprdtl_id=lp_return_dtl,
                        item_id=item_instance,
                        stock_qty=float(return_qty) if float(return_qty) > 0 else 0,
                        is_cancel_qty=float(is_cancel_qty) if float(is_cancel_qty) > 0 else 0,
                        store_id=store_instance,
                        item_batch=item_batch,
                        is_approved=is_returned_ind,
                        approved_date=returned_date_ind,
                        recon_type=False,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )
                    stock_data.save()

                    #############
                    # Get or create the cash_on_hands record
                    if lp_instance.is_cash == 1 or True:
                        cashOnHands, created = cash_on_hands.objects.get_or_create(
                            org_id=org_instance,
                            branch_id=branch_instance,
                            defaults={'on_hand_cash': 0}
                        )

                        # Calculate the amount for return or cancellation
                        def calculate_final_amount(qty, price, discount):
                            total_amt = qty * price
                            total_discount_amt = total_amt * (discount / 100)
                            return total_amt - total_discount_amt

                        # If there is a return quantity
                        if float(return_qty) > 0:
                            final_amt = calculate_final_amount(float(return_qty), unit_price, dis_perc)
                            # Add the final amount to on-hand cash
                            cashOnHands.on_hand_cash = F('on_hand_cash') + final_amt

                        # If there is a cancel quantity
                        elif float(is_cancel_qty) > 0:
                            final_amt = calculate_final_amount(float(is_cancel_qty), unit_price, dis_perc)
                            # Subtract the final amount from on-hand cash
                            cashOnHands.on_hand_cash = F('on_hand_cash') - final_amt

                        # Save and refresh the cashOnHands record
                        cashOnHands.save()
                        cashOnHands.refresh_from_db()

                    # Update stock quantity in the in_stock model
                    in_stock_obj, _ = in_stock.objects.get_or_create(
                        item_id=item_instance, store_id=store_instance, defaults={'stock_qty': 0}
                    )
                    if float(return_qty) > 0:
                        in_stock_obj.stock_qty -= float(return_qty)
                    elif float(is_cancel_qty) > 0:
                        in_stock_obj.stock_qty += float(is_cancel_qty)
                    in_stock_obj.save()

                # Update local purchase instance
                lp_instance.returned_date = returned_date
                lp_instance.is_returned = is_returned
                lp_instance.is_returned_by = user_instance
                lp_instance.ss_modifier = request.user
                lp_instance.save()

                return JsonResponse({'msg': 'LP Return details saved successfully.'})

        except Exception as e:
            # Log the exception for easier debugging
            print(f"Error: {str(e)}")
            return JsonResponse({'errmsg': str(e)}, status=500)

    return JsonResponse({'errmsg': 'Invalid request method.'}, status=405)