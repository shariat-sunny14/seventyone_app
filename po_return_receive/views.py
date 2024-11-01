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
from stock_list.models import in_stock, stock_lists
from purchase_order.models import purchase_order_list, purchase_orderdtls
from po_receive.models import po_receive_details
from po_return.models import po_return_details
from po_return_receive.models import po_return_received_details
from stock_list.stock_qty import get_available_qty
from user_setup.models import store_access
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()


# po Receive Manager
@login_required()
def POReturnReceiveManagerAPI(request):
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

    return render(request, 'po_return_receive/po_return_receive_list.html', context)


# po Return Received list details
@login_required()
def getPOReturnReceiveListAPI(request):
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
        filter_kwargs &= Q(is_return_received=True)
    elif pol_option == 'false':
        filter_kwargs &= Q(is_return_received=False)

    # Add date range filter conditions
    if po_start:
        start_date = datetime.strptime(po_start, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__gte=start_date)
    if po_end:
        end_date = datetime.strptime(po_end, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__lte=end_date)

    po_data = purchase_order_list.objects.filter(is_approved=True, is_returned=True).filter(filter_kwargs)

    data = []
    for po_list in po_data:
        org_name = po_list.id_org.org_name if po_list.id_org else None
        branch_name = po_list.branch_id.branch_name if po_list.branch_id else None
        store_name = po_list.store_id.store_name if po_list.store_id else None
        supplier_name = po_list.supplier_id.supplier_name if po_list.supplier_id else None
        is_return_received_by_first = po_list.is_return_received_by.first_name if po_list.is_return_received_by is not None else ""
        is_return_received_by_last = po_list.is_return_received_by.last_name if po_list.is_return_received_by is not None else ""
        return_received_date = po_list.return_received_date if po_list.return_received_date is not None else ""
        data.append({
            'po_id': po_list.po_id,
            'po_no': po_list.po_no,
            'transaction_date': po_list.transaction_date,
            'return_received_date': return_received_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'supplier_name': supplier_name,
            'is_return_received': po_list.is_return_received,
            'is_return_received_by_first': is_return_received_by_first,
            'is_return_received_by_last': is_return_received_by_last,
        })

    return JsonResponse({'data': data})


# purchase order Return Receive
@login_required()
def purchaseOrderReturnReceivedAPI(request, po_id=None):
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    # Get the list of main stores ordered by store_no
    store_data = store.objects.filter(is_main_store=1).order_by('store_no')
    # Get approved without GRN details
    ops_Data = purchase_order_list.objects.get(pk=po_id) if po_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = po_return_details.objects.filter(po_id=ops_Data).all()

    order_details = purchase_orderdtls.objects.filter(po_id=ops_Data).all()

    # Filter the store_data to exclude the currently selected store
    if ops_Data:
        store_data = store_data.exclude(store_id=ops_Data.store_id.store_id)

    item_with_opsDtls = []
    total_grandQty = 0
    grandPoRecQty = 0
    grandPoReturnQty = 0
    grandPoReturnRecQty = 0

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        po_id_instance = ops_Data.po_id if ops_Data else None
        invoice_details = invoicedtl_list.objects.filter(item_id=item, store_id=store_instance).all()
        PORecQtyDetails = po_receive_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        POReturnQtyDetails = po_return_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        POReturnReceiveQtyDetails = po_return_received_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        
        # po_return_receive_details qty
        totalPoReturnRecQty = POReturnReceiveQtyDetails.aggregate(
            totalPoReturnRecQty=Sum(ExpressionWrapper(
                F('ret_rec_qty'), output_field=IntegerField())
            )
        )['totalPoReturnRecQty']

        if totalPoReturnRecQty is None:
            totalPoReturnRecQty = 0
        # 

        # po_receive_details rec qty
        totalPoRecQty = PORecQtyDetails.aggregate(
            totalPoRecQty=Sum(ExpressionWrapper(
                F('receive_qty'), output_field=IntegerField())
            )
        )['totalPoRecQty']

        if totalPoRecQty is None:
            totalPoRecQty = 0

        # po_returned_details qty
        totalPoReturnQty = POReturnQtyDetails.aggregate(
            totalPoReturnQty=Sum(ExpressionWrapper(
                F('return_qty'), output_field=IntegerField())
            )
        )['totalPoReturnQty']

        if totalPoReturnQty is None:
            totalPoReturnQty = 0

        available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id)
        total_grandQty += available_qty

        # 
        grandPoRecQty += totalPoRecQty
        grandPoReturnQty += totalPoReturnQty
        grandPoReturnRecQty += totalPoReturnRecQty

        # Find the associated grn_dtls for this item
        ops_dtls = None
        for dtls in opsdtl_data:
            if dtls.item_id == item:
                ops_dtls = dtls
                break
        # Find the associated order details for this item
        order_qty = None
        for order_detail in order_details:
            if order_detail.item_id == item:
                order_qty = order_detail.order_qty
                unit_price = order_detail.unit_price
                break

        if ops_dtls:
            item_with_opsDtls.append({
                'grandQty': available_qty,
                'ops_dtls': ops_dtls,
                'totalPoRecQty': totalPoRecQty,
                'totalPoReturnQty': totalPoReturnQty,
                'totalPoReturnRecQty': totalPoReturnRecQty,
                'order_qty': order_qty,
                'unit_price': unit_price,
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'po_return_receive/po_return_receive.html', context)


# save purchase oprder return receive
@login_required()
def savePOReturnReceivedAPI(request):
    if request.method == 'POST':
        retn_rec_date = request.POST.get('retn_rec_date')
        is_retn_rec = request.POST.get('is_retn_rec')
        is_retn_rec_by = request.POST.get('is_retn_rec_by')
        return_recd_remarks = request.POST.get('return_recd_remarks')
        po_id = request.POST.get('po_id')
        current_store_id = request.POST.get('current_store')
        item_ids = request.POST.getlist('item_id[]')
        retn_rec_qtys = request.POST.getlist('retn_rec_qty[]')
        item_batchs = request.POST.getlist('item_batchs[]')
        item_exp_dates = request.POST.getlist('item_exp_dates[]')
        is_retn_rec_inds = request.POST.getlist('is_retn_rec_ind[]')
        retn_rec_date_ind = request.POST.get('retn_rec_date_ind')

        with transaction.atomic():
            try:
                # Check if the user exists
                user_instance = None
                if is_retn_rec_by:
                    user_instance = User.objects.get(user_id=is_retn_rec_by)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)
        
            try:
                # Retrieve the purchase order instance
                po_instance = purchase_order_list.objects.get(pk=po_id)
                store_instance = store.objects.get(pk=current_store_id)
            except (purchase_order_list.DoesNotExist, store.DoesNotExist):
                return JsonResponse({'errmsg': 'Purchase order or store not found.'}, status=404)
                
            # Iterate through the received items and save them
            for item_id, retn_rec_qty, is_retn_rec_ind, item_batch, item_exp_date in zip(item_ids, retn_rec_qtys, is_retn_rec_inds, item_batchs, item_exp_dates):
                try:
                    # Retrieve the item instance
                    item_instance = items.objects.get(item_id=item_id)

                    if int(retn_rec_qty) > 0:
                        po_return_rec_detail = po_return_received_details(
                            po_id=po_instance,
                            store_id=store_instance,
                            item_id=item_instance,
                            ret_rec_qty=retn_rec_qty,
                            item_batch=item_batch,
                            item_exp_date=item_exp_date,
                            is_return_received=is_retn_rec_ind,
                            return_received_date=retn_rec_date_ind,
                            is_return_received_by=request.user,
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                        po_return_rec_detail.save()

                        # Update or create stock_lists
                        stock_data = stock_lists(
                            po_id=po_instance,
                            porrecdtl_id=po_return_rec_detail,
                            item_id=item_instance,
                            stock_qty=retn_rec_qty,
                            store_id=store_instance,
                            item_batch=item_batch,
                            item_exp_date=item_exp_date,
                            is_approved=is_retn_rec_ind,
                            approved_date=retn_rec_date_ind,
                            recon_type=True, #recon_type=True is adding item in stock list
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                        stock_data.save()

                        in_stock_obj, created = in_stock.objects.get_or_create(
                            item_id=item_instance,
                            store_id=store_instance,
                            defaults={
                                'stock_qty': retn_rec_qty,
                            }
                        )
                        if not created:
                            # If the record exists, update the stock_qty
                            in_stock_obj.stock_qty += float(retn_rec_qty)
                            in_stock_obj.save()

                except items.DoesNotExist:
                    return JsonResponse({'errmsg': f'Item with ID {item_id} not found.'}, status=404)

            # Update the purchase order list
            try:
                updatepo_list = purchase_order_list.objects.get(po_id=po_id)
                if updatepo_list.is_return_received:
                    return JsonResponse({'success': False, 'errmsg': 'Already PO Return Receive Approved!'})
                
                updatepo_list.return_received_date = retn_rec_date
                updatepo_list.is_return_received = is_retn_rec
                updatepo_list.is_return_received_by = user_instance
                updatepo_list.return_received_remarks = return_recd_remarks
                updatepo_list.ss_modifier = request.user
                updatepo_list.save()

                return JsonResponse({'msg': 'PO Return Receive details saved successfully.'})
            except purchase_order_list.DoesNotExist:
                return JsonResponse({'errmsg': 'Purchase order not found.'}, status=404)
            except Exception as e:
                return JsonResponse({'errmsg': str(e)}, status=500)
    else:
        return JsonResponse({'errmsg': 'Invalid request method.'}, status=405)


# purchase order Return Receive Report
@login_required()
def POReturnReceivedReportAPI(request, po_id=None):
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    # Get the list of main stores ordered by store_no
    store_data = store.objects.filter(is_main_store=1).order_by('store_no')
    # Get approved without GRN details
    ops_Data = purchase_order_list.objects.get(pk=po_id) if po_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = po_return_details.objects.filter(po_id=ops_Data).all()

    order_details = purchase_orderdtls.objects.filter(po_id=ops_Data).all()

    # Filter the store_data to exclude the currently selected store
    if ops_Data:
        store_data = store_data.exclude(store_id=ops_Data.store_id.store_id)

    item_with_opsDtls = []
    total_grandQty = 0
    grandPoRecQty = 0
    grandPoReturnQty = 0
    grandPoReturnRecQty = 0

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        po_id_instance = ops_Data.po_id if ops_Data else None
        invoice_details = invoicedtl_list.objects.filter(item_id=item, store_id=store_instance).all()
        PORecQtyDetails = po_receive_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        POReturnQtyDetails = po_return_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        POReturnReceiveQtyDetails = po_return_received_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        
        # po_return_receive_details qty
        totalPoReturnRecQty = POReturnReceiveQtyDetails.aggregate(
            totalPoReturnRecQty=Sum(ExpressionWrapper(
                F('ret_rec_qty'), output_field=IntegerField())
            )
        )['totalPoReturnRecQty']

        if totalPoReturnRecQty is None:
            totalPoReturnRecQty = 0
        # 

        # po_receive_details rec qty
        totalPoRecQty = PORecQtyDetails.aggregate(
            totalPoRecQty=Sum(ExpressionWrapper(
                F('receive_qty'), output_field=IntegerField())
            )
        )['totalPoRecQty']

        if totalPoRecQty is None:
            totalPoRecQty = 0

        # po_returned_details qty
        totalPoReturnQty = POReturnQtyDetails.aggregate(
            totalPoReturnQty=Sum(ExpressionWrapper(
                F('return_qty'), output_field=IntegerField())
            )
        )['totalPoReturnQty']

        if totalPoReturnQty is None:
            totalPoReturnQty = 0

        available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id)
        total_grandQty += available_qty

        # 
        grandPoRecQty += totalPoRecQty
        grandPoReturnQty += totalPoReturnQty
        grandPoReturnRecQty += totalPoReturnRecQty

        # Find the associated grn_dtls for this item
        ops_dtls = None
        for dtls in opsdtl_data:
            if dtls.item_id == item:
                ops_dtls = dtls
                break
        # Find the associated order details for this item
        order_qty = None
        for order_detail in order_details:
            if order_detail.item_id == item:
                order_qty = order_detail.order_qty
                unit_price = order_detail.unit_price
                break

        if ops_dtls:
            item_with_opsDtls.append({
                'grandQty': available_qty,
                'ops_dtls': ops_dtls,
                'totalPoRecQty': totalPoRecQty,
                'totalPoReturnQty': totalPoReturnQty,
                'totalPoReturnRecQty': totalPoReturnRecQty,
                'order_qty': order_qty,
                'unit_price': unit_price,
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'po_return_receive/po_return_receive_report.html', context)