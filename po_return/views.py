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
from stock_list.stock_qty import get_available_qty
from user_setup.models import store_access
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()


# po Receive Manager
@login_required()
def POReturnManagerAPI(request):
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

    return render(request, 'po_return/po_return_list.html', context)


# po Received list details
@login_required()
def getPurchaseOrderReturnListAPI(request):
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
        filter_kwargs &= Q(is_returned=True)
    elif pol_option == 'false':
        filter_kwargs &= Q(is_returned=False)

    # Add date range filter conditions
    if po_start:
        start_date = datetime.strptime(po_start, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__gte=start_date)
    if po_end:
        end_date = datetime.strptime(po_end, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__lte=end_date)

    po_data = purchase_order_list.objects.filter(is_approved=True, is_received=True).filter(filter_kwargs)

    data = []
    for po_list in po_data:
        org_name = po_list.id_org.org_name if po_list.id_org else None
        branch_name = po_list.branch_id.branch_name if po_list.branch_id else None
        store_name = po_list.store_id.store_name if po_list.store_id else None
        supplier_name = po_list.supplier_id.supplier_name if po_list.supplier_id else None
        is_returned_by_first = po_list.is_returned_by.first_name if po_list.is_returned_by is not None else ""
        is_returned_by_last = po_list.is_returned_by.last_name if po_list.is_returned_by is not None else ""
        returned_date = po_list.returned_date if po_list.returned_date is not None else ""
        data.append({
            'po_id': po_list.po_id,
            'po_no': po_list.po_no,
            'transaction_date': po_list.transaction_date,
            'returned_date': returned_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'supplier_name': supplier_name,
            'is_returned': po_list.is_returned,
            'is_returned_by_first': is_returned_by_first,
            'is_returned_by_last': is_returned_by_last,
        })

    return JsonResponse({'data': data})



# purchase order Return
@login_required()
def purchaseOrderReturnAPI(request, po_id=None):
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    # Get the list of main stores ordered by store_no
    store_data = store.objects.filter(is_main_store=1).order_by('store_no')
    # Get approved without GRN details
    ops_Data = purchase_order_list.objects.get(pk=po_id) if po_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = po_receive_details.objects.filter(po_id=ops_Data).all()

    order_details = purchase_orderdtls.objects.filter(po_id=ops_Data).all()

    # Filter the store_data to exclude the currently selected store
    if ops_Data:
        store_data = store_data.exclude(store_id=ops_Data.store_id.store_id)

    item_with_opsDtls = []
    total_grandQty = 0
    grandPoRecQty = 0
    grandPoReturnQty = 0

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        po_id_instance = ops_Data.po_id if ops_Data else None
        invoice_details = invoicedtl_list.objects.filter(item_id=item, store_id=store_instance).all()
        PORecQtyDetails = po_receive_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        POReturnQtyDetails = po_return_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        # po_receive_details rec qty
        totalPoRecQty = PORecQtyDetails.aggregate(
            totalPoRecQty=Sum(ExpressionWrapper(
                F('receive_qty'), output_field=FloatField())
            )
        )['totalPoRecQty']

        if totalPoRecQty is None:
            totalPoRecQty = 0

        # po_returned_details qty
        totalPoReturnQty = POReturnQtyDetails.aggregate(
            totalPoReturnQty=Sum(ExpressionWrapper(
                F('return_qty'), output_field=FloatField())
            )
        )['totalPoReturnQty']

        if totalPoReturnQty is None:
            totalPoReturnQty = 0

        # 
        grandPoRecQty += totalPoRecQty
        grandPoReturnQty += totalPoReturnQty

        available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id)
        total_grandQty += available_qty

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
                'order_qty': order_qty,
                'unit_price': unit_price,
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'po_return/po_return.html', context)


@login_required()
def savePurchaseOrderReturnedAPI(request):
    if request.method == 'POST':
        # Extracting data from the request
        returned_date = request.POST.get('returned_date')
        is_returned = request.POST.get('is_returned')
        is_returned_by = request.POST.get('is_returned_by')
        returned_remarks = request.POST.get('returned_remarks')
        po_id = request.POST.get('po_id')
        current_store_id = request.POST.get('current_store')
        item_ids = request.POST.getlist('item_id[]')
        return_qtys = request.POST.getlist('return_qty[]')
        item_batchs = request.POST.getlist('item_batchs[]')
        item_exp_dates = request.POST.getlist('item_exp_dates[]')
        is_returned_inds = request.POST.getlist('is_returned_ind[]')
        returned_date_ind = request.POST.get('returned_date_ind')

        with transaction.atomic():
            try:
                # Check if the user exists
                user_instance = None
                if is_returned_by:
                    user_instance = User.objects.get(user_id=is_returned_by)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)
        
            try:
                # Retrieve the purchase order instance
                po_instance = purchase_order_list.objects.get(pk=po_id)
                store_instance = store.objects.get(pk=current_store_id)
            except (purchase_order_list.DoesNotExist, store.DoesNotExist):
                return JsonResponse({'errmsg': 'Purchase order or store not found.'}, status=404)
                
            # Iterate through the received items and save them
            for item_id, return_qty, is_returned_ind, item_batch, item_exp_date in zip(item_ids, return_qtys, is_returned_inds, item_batchs, item_exp_dates):
                try:
                    # Retrieve the item instance
                    item_instance = items.objects.get(item_id=item_id)

                    if int(return_qty) > 0:
                        po_reteru_detail = po_return_details(
                            po_id=po_instance,
                            store_id=store_instance,
                            item_id=item_instance,
                            return_qty=return_qty,
                            item_batch=item_batch,
                            item_exp_date=item_exp_date,
                            is_returned=is_returned_ind,
                            returned_date=returned_date_ind,
                            is_returned_by=request.user,
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                        po_reteru_detail.save()

                        # Update or create stock_lists
                        stock_data = stock_lists(
                            po_id=po_instance,
                            poretdtl_id=po_reteru_detail,
                            item_id=item_instance,
                            stock_qty=return_qty,
                            store_id=store_instance,
                            item_batch=item_batch,
                            item_exp_date=item_exp_date,
                            is_approved=is_returned_ind,
                            approved_date=returned_date_ind,
                            recon_type=False, #recon_type=False, cause this stock list another module no need to effect
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                        stock_data.save()

                        # stock minus in the in_stock models
                        in_stock_obj, created = in_stock.objects.get_or_create(
                            item_id=item_instance,
                            store_id=store_instance,
                            defaults={
                                'stock_qty': return_qty,
                            }
                        )
                        if not created:
                            # If the record exists, update the stock_qty
                            in_stock_obj.stock_qty -= float(return_qty)
                            in_stock_obj.save()

                except items.DoesNotExist:
                    return JsonResponse({'errmsg': f'Item with ID {item_id} not found.'}, status=404)

            # Update the purchase order list
            try:
                updatepo_list = purchase_order_list.objects.get(po_id=po_id)
                if updatepo_list.is_returned:
                    return JsonResponse({'success': False, 'errmsg': 'Already PO Returned Approved!'})
                
                updatepo_list.returned_date = returned_date
                updatepo_list.is_returned = is_returned
                updatepo_list.is_returned_by = user_instance
                updatepo_list.returned_remarks = returned_remarks
                updatepo_list.ss_modifier = request.user
                updatepo_list.save()

                return JsonResponse({'msg': 'PO Return details saved successfully.'})
            except purchase_order_list.DoesNotExist:
                return JsonResponse({'errmsg': 'Purchase order not found.'}, status=404)
            except Exception as e:
                return JsonResponse({'errmsg': str(e)}, status=500)
    else:
        return JsonResponse({'errmsg': 'Invalid request method.'}, status=405)


# purchase order Returned Report
@login_required()
def POReturnedReportAPI(request, po_id=None):
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    # Get the list of main stores ordered by store_no
    store_data = store.objects.filter(is_main_store=1).order_by('store_no')
    # Get approved without GRN details
    ops_Data = purchase_order_list.objects.get(pk=po_id) if po_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = po_receive_details.objects.filter(po_id=ops_Data).all()

    order_details = purchase_orderdtls.objects.filter(po_id=ops_Data).all()

    # Filter the store_data to exclude the currently selected store
    if ops_Data:
        store_data = store_data.exclude(store_id=ops_Data.store_id.store_id)

    item_with_opsDtls = []
    total_grandQty = 0
    grandPoRecQty = 0
    grandPoReturnQty = 0

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        po_id_instance = ops_Data.po_id if ops_Data else None
        invoice_details = invoicedtl_list.objects.filter(item_id=item, store_id=store_instance).all()
        PORecQtyDetails = po_receive_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        POReturnQtyDetails = po_return_details.objects.filter(item_id=item, po_id=po_id_instance).all()
        
        # po_receive_details rec qty
        totalPoRecQty = PORecQtyDetails.aggregate(
            totalPoRecQty=Sum(ExpressionWrapper(
                F('receive_qty'), output_field=FloatField())
            )
        )['totalPoRecQty']

        if totalPoRecQty is None:
            totalPoRecQty = 0

        # po_returned_details qty
        totalPoReturnQty = POReturnQtyDetails.aggregate(
            totalPoReturnQty=Sum(ExpressionWrapper(
                F('return_qty'), output_field=FloatField())
            )
        )['totalPoReturnQty']

        if totalPoReturnQty is None:
            totalPoReturnQty = 0

        # 
        grandPoRecQty += totalPoRecQty
        grandPoReturnQty += totalPoReturnQty

        available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id)
        total_grandQty += available_qty

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
                'order_qty': order_qty,
                'unit_price': unit_price,
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'po_return/po_return_report.html', context)