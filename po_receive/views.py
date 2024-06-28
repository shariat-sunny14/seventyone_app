import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField
from django.db import transaction
from datetime import datetime
from django.core import serializers
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from others_setup.models import item_type
from store_setup.models import store
from organizations.models import branchslist, organizationlst
from item_setup.models import items
from opening_stock.models import opening_stock
from item_pos.models import invoicedtl_list
from stock_list.models import stock_lists
from purchase_order.models import purchase_order_list, purchase_orderdtls
from po_receive.models import po_receive_details
from stock_list.stock_qty import get_available_qty
from user_setup.models import store_access
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()

# po Receive Manager
@login_required()
def POReceiveManagerAPI(request):
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

    return render(request, 'po_receive/po_receive_list.html', context)

# po Received list details
@login_required()
def getPurchaseOrderReceivedListAPI(request):
    pol_option = request.GET.get('pol_option')
    org_id_wise_filter = request.GET.get('filter_org', '')
    branch_id_wise_filter = request.GET.get('filter_branch', '')
    po_start = request.GET.get('po_start')
    po_end = request.GET.get('po_end')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(id_org=org_id_wise_filter)
    
    if branch_id_wise_filter:
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)

    # Add is_active filter condition based on typeoption
    if pol_option == 'true':
        filter_kwargs &= Q(is_received=True)
    elif pol_option == 'false':
        filter_kwargs &= Q(is_received=False)

    # Add date range filter conditions
    if po_start:
        start_date = datetime.strptime(po_start, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__gte=start_date)
    if po_end:
        end_date = datetime.strptime(po_end, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__lte=end_date)

    po_data = purchase_order_list.objects.filter(is_approved=True).filter(filter_kwargs)

    data = []
    for po_list in po_data:
        org_name = po_list.id_org.org_name if po_list.id_org else None
        branch_name = po_list.branch_id.branch_name if po_list.branch_id else None
        store_name = po_list.store_id.store_name if po_list.store_id else None
        supplier_name = po_list.supplier_id.supplier_name if po_list.supplier_id else None
        is_received_by_first = po_list.is_received_by.first_name if po_list.is_received_by is not None else ""
        is_received_by_last = po_list.is_received_by.last_name if po_list.is_received_by is not None else ""
        received_date = po_list.received_date if po_list.received_date is not None else ""
        data.append({
            'po_id': po_list.po_id,
            'po_no': po_list.po_no,
            'transaction_date': po_list.transaction_date,
            'received_date': received_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'supplier_name': supplier_name,
            'is_received': po_list.is_received,
            'is_received_by_first': is_received_by_first,
            'is_received_by_last': is_received_by_last,
        })

    return JsonResponse({'data': data})



# purchase order Received Item Details list
@login_required()
def POReceivedItemDetailsListAPI(request, po_id=None):
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    # Get the list of main stores ordered by store_no
    store_data = store.objects.filter(is_main_store=1).order_by('store_no')
    # Get approved without GRN details
    ops_Data = purchase_order_list.objects.get(pk=po_id) if po_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = purchase_orderdtls.objects.filter(po_id=ops_Data).all()

    # Filter the store_data to exclude the currently selected store
    if ops_Data:
        store_data = store_data.exclude(store_id=ops_Data.store_id.store_id)

    item_with_opsDtls = []
    total_grandQty = 0
    grandPoRecQty = 0
    grandRecBonusQty = 0

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        po_id_instance = ops_Data.po_id if ops_Data else None
        PORecQtyDetails = po_receive_details.objects.filter(item_id=item, po_id=po_id_instance).all()

        # po_receive_details rec qty
        totalPoRecQty = PORecQtyDetails.aggregate(
            totalPoRecQty=Sum(ExpressionWrapper(
                F('receive_qty'), output_field=IntegerField())
            )
        )['totalPoRecQty']

        if totalPoRecQty is None:
            totalPoRecQty = 0

        # po_receive_details bonus qty
        totRecBonusQty = PORecQtyDetails.aggregate(
            totRecBonusQty=Sum(ExpressionWrapper(
                F('bonus_qty'), output_field=IntegerField())
            )
        )['totRecBonusQty']

        if totRecBonusQty is None:
            totRecBonusQty = 0

        # 
        grandPoRecQty += totalPoRecQty
        grandRecBonusQty += totRecBonusQty

        available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id)
        total_grandQty += available_qty

        # Find the associated grn_dtls for this item
        ops_dtls = None
        for dtls in opsdtl_data:
            if dtls.item_id == item:
                ops_dtls = dtls
                break
        if ops_dtls:
            item_with_opsDtls.append({
                'grandQty': available_qty,
                'ops_dtls': ops_dtls,
                'totalPoRecQty': totalPoRecQty,
                'totRecBonusQty': totRecBonusQty,
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'po_receive/po_receive_item_details.html', context)


@login_required()
def recievedPODetailsListAPI(request):
    if request.method == 'POST':
        # Extracting data from the request
        received_date = request.POST.get('received_date')
        is_received = request.POST.get('is_received')
        is_received_by = request.POST.get('is_received_by')
        received_remarks = request.POST.get('received_remarks')
        po_id = request.POST.get('po_id')
        current_store_id = request.POST.get('current_store')
        item_ids = request.POST.getlist('item_id[]')
        received_qtys = request.POST.getlist('receive_qty[]')
        bonus_qtys = request.POST.getlist('bonus_qty[]')
        is_received_inds = request.POST.getlist('is_received_ind[]')
        received_date_ind = request.POST.get('received_date_ind')

        with transaction.atomic():
            try:
                # Check if the user exists
                user_instance = None
                if is_received_by:
                    user_instance = User.objects.get(user_id=is_received_by)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)
        
            try:
                # Retrieve the purchase order instance
                po_instance = purchase_order_list.objects.get(pk=po_id)
                store_instance = store.objects.get(pk=current_store_id)
            except (purchase_order_list.DoesNotExist, store.DoesNotExist):
                return JsonResponse({'errmsg': 'Purchase order or store not found.'}, status=404)
                
            # Iterate through the received items and save them
            for item_id, receive_qty, bonus_qty, is_received_ind in zip(item_ids, received_qtys, bonus_qtys, is_received_inds):
                try:
                    # Retrieve the item instance
                    item_instance = items.objects.get(item_id=item_id)
                    # Calculate total quantity (receive_qty + bonus_qty)
                    total_qty = int(receive_qty) + int(bonus_qty)

                    # Check if either receive_qty or bonus_qty is greater than 0
                    if int(receive_qty) > 0 or int(bonus_qty) > 0:
                        # Create and save po_receive_details object
                        po_receive_detail = po_receive_details(
                            po_id=po_instance,
                            store_id=store_instance,
                            item_id=item_instance,
                            receive_qty=receive_qty,
                            bonus_qty=bonus_qty,
                            is_received=is_received_ind,
                            received_date=received_date_ind,
                            is_received_by=request.user,
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                        po_receive_detail.save()

                        # Update or create stock_lists
                        stock_data = stock_lists(
                            po_id=po_instance,
                            pordtl_id=po_receive_detail,
                            item_id=item_instance,
                            stock_qty=total_qty,
                            store_id=store_instance,
                            is_approved=is_received_ind,
                            approved_date=received_date_ind,
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                        stock_data.save()
                    
                except items.DoesNotExist:
                    return JsonResponse({'errmsg': f'Item with ID {item_id} not found.'}, status=404)

            # Update the purchase order list
            try:
                updatepo_list = purchase_order_list.objects.get(po_id=po_id)
                if updatepo_list.is_received:
                    return JsonResponse({'success': False, 'errmsg': 'Already PO Receive Approved!'})
                
                updatepo_list.received_date = received_date
                updatepo_list.is_received = is_received
                updatepo_list.is_received_by = user_instance
                updatepo_list.received_remarks = received_remarks
                updatepo_list.ss_modifier = request.user
                updatepo_list.save()

                return JsonResponse({'msg': 'Received details saved successfully.'})
            except purchase_order_list.DoesNotExist:
                return JsonResponse({'errmsg': 'Purchase order not found.'}, status=404)
            except Exception as e:
                return JsonResponse({'errmsg': str(e)}, status=500)
    else:
        return JsonResponse({'errmsg': 'Invalid request method.'}, status=405)



@login_required()
def POReceivedReportAPI(request, po_id=None):
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    # Get the list of main stores ordered by store_no
    store_data = store.objects.filter(is_main_store=1).order_by('store_no')
    # Get approved without GRN details
    ops_Data = purchase_order_list.objects.get(pk=po_id) if po_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = purchase_orderdtls.objects.filter(po_id=ops_Data).all()

    # Filter the store_data to exclude the currently selected store
    if ops_Data:
        store_data = store_data.exclude(store_id=ops_Data.store_id.store_id)

    item_with_opsDtls = []
    total_grandQty = 0
    grandPoRecQty = 0
    grandRecBonusQty = 0

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        po_id_instance = ops_Data.po_id if ops_Data else None
        PORecQtyDetails = po_receive_details.objects.filter(item_id=item, po_id=po_id_instance).all()

        # po_receive_details rec qty
        totalPoRecQty = PORecQtyDetails.aggregate(
            totalPoRecQty=Sum(ExpressionWrapper(
                F('receive_qty'), output_field=IntegerField())
            )
        )['totalPoRecQty']

        if totalPoRecQty is None:
            totalPoRecQty = 0

        # po_receive_details bonus qty
        totRecBonusQty = PORecQtyDetails.aggregate(
            totRecBonusQty=Sum(ExpressionWrapper(
                F('bonus_qty'), output_field=IntegerField())
            )
        )['totRecBonusQty']

        if totRecBonusQty is None:
            totRecBonusQty = 0

        # 
        grandPoRecQty += totalPoRecQty
        grandRecBonusQty += totRecBonusQty

        available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id)
        total_grandQty += available_qty

        # Find the associated grn_dtls for this item
        ops_dtls = None
        for dtls in opsdtl_data:
            if dtls.item_id == item:
                ops_dtls = dtls
                break
        if ops_dtls:
            item_with_opsDtls.append({
                'grandQty': available_qty,
                'ops_dtls': ops_dtls,
                'totalPoRecQty': totalPoRecQty,
                'totRecBonusQty': totRecBonusQty,
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'po_receive/po_receive_report.html', context)