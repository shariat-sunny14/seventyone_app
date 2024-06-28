import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField
from django.db import transaction
from django.contrib import messages
from item_setup.models import items
from store_setup.models import store
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from stock_list.stock_qty import get_available_qty
from supplier_setup.models import suppliers
from . models import without_GRN, without_GRNdtl
from stock_list.models import stock_lists
from item_pos.models import invoicedtl_list
from opening_stock.models import opening_stockdtl
from others_setup.models import item_type
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def without_GRN_listAPI(request):
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
    return render(request, 'G_R_N_with_without/without_grn_list.html', context)

@login_required()
def getWGRNListDetailsAPI(request):
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
        filter_kwargs &= Q(is_approved=True)
    elif pol_option == 'false':
        filter_kwargs &= Q(is_approved=False)

    # Add date range filter conditions
    if po_start:
        start_date = datetime.strptime(po_start, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__gte=start_date)
    if po_end:
        end_date = datetime.strptime(po_end, '%Y-%m-%d')
        filter_kwargs &= Q(transaction_date__lte=end_date)

    wo_grn_data = without_GRN.objects.filter(filter_kwargs)

    data = []

    for wo_grn_list in wo_grn_data:
        org_name = wo_grn_list.id_org.org_name if wo_grn_list.id_org else None
        branch_name = wo_grn_list.branch_id.branch_name if wo_grn_list.branch_id else None
        store_name = wo_grn_list.store_id.store_name if wo_grn_list.store_id else None
        is_approved_by_first = wo_grn_list.is_approved_by.first_name if wo_grn_list.is_approved_by is not None else ""
        is_approved_by_last = wo_grn_list.is_approved_by.last_name if wo_grn_list.is_approved_by is not None else ""
        data.append({
            'wo_grn_id': wo_grn_list.wo_grn_id,
            'wo_grn_no': wo_grn_list.wo_grn_no,
            'transaction_date': wo_grn_list.transaction_date,
            'approved_date': wo_grn_list.approved_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'is_approved': wo_grn_list.is_approved,
            'is_approved_by_first': is_approved_by_first,
            'is_approved_by_last': is_approved_by_last,
        })

    return JsonResponse({'data': data})


# add receive stock without grn
@login_required()
def recStockwithout_GRNAPI(request, id=0):
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

    return render(request, 'G_R_N_with_without/add_rec_stock_withoutgrn.html', context)

# get receive stock without grn list
@login_required()
def get_recStckwithout_GRNAPI(request):
    selected_type_id = request.GET.get('selectedTypeId')
    store_id = request.GET.get('store_id')  # Fetch the store_id from the request
    selected_id_org = request.GET.get('id_org')
    selected_supplier_id = request.GET.get('filter_suppliers')

    item_with_grandQty = []

    # Get a list of distinct item IDs from opening stock details with is_approved and specific store_id
    op_stock_item_ids = opening_stockdtl.objects.filter(is_approved=True, store_id=store_id).values_list('item_id', flat=True).distinct()

    # Iterate through each distinct item ID
    for item_id in op_stock_item_ids:
        # Filter items related to each item_id from opening_stockdtl
        item_data = items.objects.filter(item_id=item_id, is_active=True)

        # Apply filtering based on selected type ID if provided
        if selected_type_id and selected_type_id != '1':
            item_data = item_data.filter(type_id=selected_type_id)
        
        if selected_id_org:
            item_data = item_data.filter(org_id=selected_id_org)

        if selected_supplier_id and selected_supplier_id != '1':
            item_data = item_data.filter(item_supplierdtl__supplier_id=selected_supplier_id)

        # Get the most recent item for the selected type
        item_data = item_data.all()

        for item in item_data:
            item_with_grandQty.append({
                'item_id': item.item_id,
                'item_name': item.item_name,
            })

    return JsonResponse({'data': item_with_grandQty})


# get receive stock without grn list details
@login_required()
def get_recStockwithout_grn_details(request):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        selected_item_id = request.GET.get('selectedItem')
        store_id = request.GET.get('store_id')
        org_id = request.GET.get('selected_id_org')
        
        try:
            selected_item = items.objects.get(item_id=selected_item_id, org_id=org_id)

            item_details = []
            
            available_qty = get_available_qty(item_id=selected_item, store_id=store_id, org_id=org_id)

            item_details.append({
                'item_id': selected_item.item_id,
                'item_no': selected_item.item_no,
                'type_name': selected_item.type_id.type_name if selected_item.type_id else '',
                'uom_name': selected_item.item_uom_id.item_uom_name if selected_item.item_uom_id else '',
                'grandQty': available_qty,
                'sales_price': selected_item.sales_price,
                'item_name': selected_item.item_name,
            })

            return JsonResponse({'data': item_details})
        except items.DoesNotExist:
            return JsonResponse({'error': 'Item not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


# edit/update receive stock without grn
@login_required()
def edit_recStockwithout_GRNAPI(request, wo_grn_id=None):
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
    
    
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    wogrn_Data = without_GRN.objects.get(pk=wo_grn_id) if wo_grn_id else None

    # Query without_GRNdtl records related to the withgrnData
    wogrndtl_data = without_GRNdtl.objects.filter(wo_grn_id=wogrn_Data).all()

    item_with_wogrnDtls = []

    for item in item_data:
        store_instance = wogrn_Data.store_id if wogrn_Data else None
        org_instance = wogrn_Data.id_org if wogrn_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)
        
        # Find the associated grn_dtls for this item
        wogrn_dtls = None
        for dtls in wogrndtl_data:
            if dtls.item_id == item:
                wogrn_dtls = dtls
                break
        if wogrn_dtls:
            item_with_wogrnDtls.append({
                'grandQty': available_qty,
                'wogrn_dtls': wogrn_dtls,
            })

    context = {
        'org_list': org_list,
        'item_with_wogrnDtls': item_with_wogrnDtls,
        'wogrn_Data': wogrn_Data,
    }

    return render(request, 'G_R_N_with_without/edit_rec_stock_withoutgrn.html', context)


@login_required()
def exsit_receiveStockWogrnAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST

    store_id = data.get("store_id")
    item_ids = data.getlist('item_ids[]')
    item_batch_name = data.getlist('item_batch')

    store_instance = store.objects.get(store_id=store_id)

    # Create a list to store error messages for existing items
    existing_items_err_msgs = []

    for item_id, item_batch in zip(item_ids, item_batch_name):
        # Fetch the item associated with the item_id
        item_instance = items.objects.get(item_id=item_id)

        # Check if an item with the same item_id exists in without_GRNdtl
        if without_GRNdtl.objects.filter(Q(item_id=item_instance) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch)).exists():
            errmsg = f"This Item: '{item_instance.item_name}' is already exists in Batch: '{item_batch}' and Store: '{store_instance.store_name}' Please.. Change the 'Batch' Name ..."
            existing_items_err_msgs.append(errmsg)

    # Check if there are any existing items
    if existing_items_err_msgs:
        # If there are existing items, return an error response
        resp['msg'] = ', '.join(existing_items_err_msgs)
    else:
        resp['status'] = 'success'

    return JsonResponse(resp)


@login_required()
def receiveStockWogrnAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    id_org = data.get("org")
    branch_id = data.get("branchs")
    store_id =data.get("current_store")
    supplier_id = data.get("supplier")
    is_approved_by_user = data.get('is_approved_by_user_id')
    is_credit = data.get('is_credit', False)
    is_cash = data.get('is_cash', False)

    item_ids = data.getlist('item_id[]')
    item_qtys = data.getlist('item_qty[]')
    item_prices = data.getlist('item_price[]')
    item_batchs = data.getlist('item_batchs[]')

    store_instance = store.objects.get(store_id=store_id)
    
    # Create a list to store error messages for existing items
    existing_items_err_msgs = []

    for item_id, item_batch_value in zip(item_ids, item_batchs):
        # Fetch the item associated with the item_id
        item_instance = items.objects.get(item_id=item_id, org_id=id_org)

        # Check if an item with the same item_id exists in opening_stockdtl
        if without_GRNdtl.objects.filter(Q(item_id=item_instance) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch_value)).exists():
            errmsg = f"This Item: '{item_instance.item_name}' is already exists in Invoice No: '{item_batch_value}' and Store: '{store_instance.store_name}' Please.. Change the 'Invoice No' ..."
            existing_items_err_msgs.append(errmsg)

    # Check if there are any existing items
    if existing_items_err_msgs:
        # If there are existing items, return an error response
        return JsonResponse({'success': False, 'errmsg': ', '.join(existing_items_err_msgs)})

    try:
        with transaction.atomic():
            try:
                # Check if the user exists
                user_instance = None
                if is_approved_by_user:
                    user_instance = User.objects.get(user_id=is_approved_by_user)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)
            
            if id_org and branch_id:
                try:
                    org_instance = organizationlst.objects.get(org_id=id_org)
                    branch_instance = branchslist.objects.get(branch_id=branch_id)
                    supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
                    # receive an without_GRN instance
                    receiveGRNstock = without_GRN(
                        id_org=org_instance,
                        branch_id=branch_instance,
                        supplier_id=supplier_instance,
                        is_cash=is_cash,
                        is_credit=is_credit,
                        store_id=store_instance,
                        transaction_date=data['transaction_date'],
                        is_approved=data['is_approved'],
                        is_approved_by=user_instance,
                        approved_date=data['approved_date'],
                        remarks=data['remarks'],
                        ss_creator=request.user
                    )
                    receiveGRNstock.save()

                    # receive without_GRNdtl instances for each item
                    for item_id, item_price, qty, batch in zip(item_ids, item_prices, item_qtys, item_batchs):
                        item_instance = items.objects.get(item_id=item_id)

                        receiveGRNstockDtl = without_GRNdtl(
                            unit_price=item_price,
                            wo_grn_qty=qty,
                            item_batch=batch,
                            item_id=item_instance,
                            wo_grn_id=receiveGRNstock,
                            store_id=store_instance,
                            supplier_id=supplier_instance,
                            wo_grn_date=receiveGRNstock.transaction_date,
                            is_approved=receiveGRNstock.is_approved,
                            approved_date=receiveGRNstock.approved_date,
                            ss_creator=request.user
                        )
                        receiveGRNstockDtl.save()

                        stock_data = stock_lists(
                            wo_grn_id=receiveGRNstock,
                            wo_grndtl_id=receiveGRNstockDtl,
                            stock_qty=qty,
                            item_batch=batch,
                            item_id=item_instance,
                            store_id=store_instance,
                            is_approved=receiveGRNstock.is_approved,
                            approved_date=receiveGRNstock.approved_date,
                            ss_creator=request.user
                        )
                        stock_data.save()

                    resp['status'] = 'success'
                    return JsonResponse({'success': True, 'msg': 'Successful'})

                except organizationlst.DoesNotExist:
                    resp['errmsg'] = 'Organization associated with the user does not exist.'
                except branchslist.DoesNotExist:
                    resp['errmsg'] = 'Branch associated with the user does not exist.'
                except suppliers.DoesNotExist:
                    resp['errmsg'] = 'Suppliers Not Selected... Please Select First!..'
            else:
                resp['errmsg'] = 'User is not associated with an organization or branch.'
    except Exception as e:
        print("Error:", str(e))
        resp['status'] = 'failed'

    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required()
def edit_receiveStockWogrnAPI(request):
    resp = {'success': False, 'errmsg': 'Fails'}
    data = request.POST

    wo_grn_id = data.get('wo_grn_id')

    if wo_grn_id.isnumeric() and int(wo_grn_id) > 0:
        id_org = data.get("org")
        branch_id = data.get("branchs")
        store_id =data.get("current_store")
        supplier_id = data.get("supplier")
        is_approved_by_user = data.get('is_approved_by_user_id')
        is_credit = data.get('is_credit', False)
        is_cash = data.get('is_cash', False)
        item_prices = data.getlist('item_price[]')
        item_ids = data.getlist('item_id[]')
        item_qtys = data.getlist('item_qty[]')
        item_batchs = data.getlist('item_batchs[]')

        try:
            # Check if the user exists
            user_instance = None
            if is_approved_by_user:
                user_instance = User.objects.get(user_id=is_approved_by_user)
        except User.DoesNotExist:
            return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)
        
        store_instance = store.objects.get(store_id=store_id)
        org_instance = organizationlst.objects.get(org_id=id_org)
        branch_instance = branchslist.objects.get(branch_id=branch_id)
        supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
        receiveGRNstock = without_GRN.objects.get(wo_grn_id=wo_grn_id)

        for item_id, item_batch_value in zip(item_ids, item_batchs):
            # Fetch the item associated with the item_id
            item_value = items.objects.get(item_id=item_id, org_id=id_org)

            # Check if the same combination of item_id, store_id, and item_batch exists in without_GRNdtl for another wo_grn_id
            existing_items = without_GRNdtl.objects.filter(
                Q(item_id=item_value) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch_value)
            ).exclude(wo_grn_id=receiveGRNstock)

            if existing_items.exists():
                errmsg = f"This Item: '{item_value.item_name}' is already exists in Invoice No: '{item_batch_value}' and Store: '{store_instance.store_name}' Plz Change the Invoice No..."
                return JsonResponse({'success': False, 'errmsg': errmsg})

    # If it's already approved
    if receiveGRNstock.is_approved:
        return JsonResponse({'success': False, 'errmsg': 'Already Approved!'})

    try:
        with transaction.atomic():
            # Update the without_GRN instance
            receiveGRNstock.store_id = store_instance
            receiveGRNstock.id_org = org_instance
            receiveGRNstock.branch_id = branch_instance
            receiveGRNstock.supplier_id = supplier_instance
            receiveGRNstock.transaction_date = data['transaction_date']
            receiveGRNstock.is_approved = data['is_approved']
            receiveGRNstock.is_approved_by = user_instance
            receiveGRNstock.approved_date = data['approved_date']
            receiveGRNstock.remarks = data['remarks']
            receiveGRNstock.is_credit = is_credit
            receiveGRNstock.is_cash = is_cash
            receiveGRNstock.ss_modifier = request.user
            receiveGRNstock.save()

            # Update or create without_GRNdtl instances for each item
            for item_id, item_price, qty, batch in zip(item_ids, item_prices, item_qtys, item_batchs):
                item_instance = items.objects.get(item_id=item_id)

                receiveGRNstockDtl, created = without_GRNdtl.objects.update_or_create(
                    wo_grn_id=receiveGRNstock,
                    item_id=item_instance,
                    defaults={
                        'wo_grn_qty': qty,
                        'item_batch': batch,
                        'store_id': store_instance,
                        'unit_price': item_price,
                        'wo_grn_date': receiveGRNstock.transaction_date,
                        'is_approved': receiveGRNstock.is_approved,
                        'approved_date': receiveGRNstock.approved_date,
                        'ss_modifier': request.user,
                    }
                )

                # Save the without_GRNdtl instance
                receiveGRNstockDtl.save()

                # Update or create stock_lists
                stock_data, created = stock_lists.objects.update_or_create(
                    wo_grn_id=receiveGRNstock,
                    wo_grndtl_id=receiveGRNstockDtl,
                    item_id=item_instance,
                    defaults={
                        'stock_qty': qty,
                        'item_batch': batch,
                        'store_id': store_instance,
                        'is_approved': receiveGRNstock.is_approved,
                        'approved_date': receiveGRNstock.approved_date,
                        'ss_modifier': request.user
                    }
                )

                # Save the stock_lists instance
                stock_data.save()

            resp['success'] = True
            return JsonResponse({'success': True, 'msg': 'Successful'})
    except Exception as e:
        print("Error:", str(e))
        resp['errmsg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")


# Report without grn
@login_required()
def reportWithoutGRNAPI(request, wo_grn_id=None):
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
    
    
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    wogrn_Data = without_GRN.objects.get(pk=wo_grn_id) if wo_grn_id else None

    # Query without_GRNdtl records related to the withgrnData
    wogrndtl_data = without_GRNdtl.objects.filter(wo_grn_id=wogrn_Data).all()

    item_with_wogrnDtls = []

    for item in item_data:
        store_instance = wogrn_Data.store_id if wogrn_Data else None
        org_instance = wogrn_Data.id_org if wogrn_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)
        
        # Find the associated grn_dtls for this item
        wogrn_dtls = None
        for dtls in wogrndtl_data:
            if dtls.item_id == item:
                wogrn_dtls = dtls
                break
        if wogrn_dtls:
            item_with_wogrnDtls.append({
                'grandQty': available_qty,
                'wogrn_dtls': wogrn_dtls,
            })

    context = {
        'org_list': org_list,
        'item_with_wogrnDtls': item_with_wogrnDtls,
        'wogrn_Data': wogrn_Data,
    }

    return render(request, 'G_R_N_with_without/report_without_grn.html', context)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def delete_wo_grn(request, wo_grndtl_id):
    if request.method == 'DELETE':
        try:
            # Get the wo_grndtl instance using wo_grndtl_id
            wo_grndtl = without_GRNdtl.objects.get(wo_grndtl_id=wo_grndtl_id)

            # Delete records related to the specified wo_grndtl
            # Make sure to use the correct model relationships
            stock_data = stock_lists.objects.filter(wo_grndtl_id=wo_grndtl)
            stock_data.delete()
            wo_grndtl.delete()

            return JsonResponse({'success': True, 'msg': f'Successfully deleted'})
        except without_GRNdtl.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'wo_grndtl_id {wo_grndtl_id} not found.'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})