import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField
from django.db import transaction
from datetime import datetime
from django.core import serializers
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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
from stock_list.stock_qty import get_available_qty
from user_setup.models import store_access
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def purchaseOrderManagerAPI(request):
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

    return render(request, 'purchase_order/purchase_order_list.html', context)

@login_required()
def getPurchaseOrderListAPI(request):
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

    po_data = purchase_order_list.objects.filter(filter_kwargs)

    data = []
    for po_list in po_data:
        org_name = po_list.id_org.org_name if po_list.id_org else None
        branch_name = po_list.branch_id.branch_name if po_list.branch_id else None
        store_name = po_list.store_id.store_name if po_list.store_id else None
        supplier_name = po_list.supplier_id.supplier_name if po_list.supplier_id else None
        is_approved_by_first = po_list.is_approved_by.first_name if po_list.is_approved_by is not None else ""
        is_approved_by_last = po_list.is_approved_by.last_name if po_list.is_approved_by is not None else ""
        data.append({
            'po_id': po_list.po_id,
            'po_no': po_list.po_no,
            'transaction_date': po_list.transaction_date,
            'approved_date': po_list.approved_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'supplier_name': supplier_name,
            'is_approved': po_list.is_approved,
            'is_approved_by_first': is_approved_by_first,
            'is_approved_by_last': is_approved_by_last,
        })

    return JsonResponse({'data': data})


@login_required()
def managePurchaseOrderAPI(request):
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

    return render(request, 'purchase_order/add_purchase_order.html', context)


@login_required()
def getPOEntrylistAPI(request):
    item_with_grandQty = []
    selected_type_id = request.GET.get('selectedTypeId')
    selected_id_org = request.GET.get('id_org')
    selected_supplier_id = request.GET.get('filter_suppliers')

    item_data = items.objects.filter(is_active=True)

    if selected_type_id and selected_type_id != '1':  # '1' represents the option 'All Item Type'
        item_data = item_data.filter(type_id=selected_type_id)

    if selected_id_org:
        item_data = item_data.filter(org_id=selected_id_org)

    if selected_supplier_id and selected_supplier_id != '1':
        item_data = item_data.filter(item_supplierdtl__supplier_id=selected_supplier_id)

    item_data = item_data.all()

    for item in item_data:
        item_with_grandQty.append({
            'item_id': item.item_id,
            'item_name': item.item_name,
        })

    return JsonResponse({'data': item_with_grandQty})

@login_required()
def get_user_stores(request):
    if request.user.is_authenticated:
        user_id = request.user.user_id
        user_stores = store_access.objects.filter(user_id=user_id, store_id__is_main_store=True).values('store_id', 'store_id__store_name')
        data = [{'store_id': store['store_id'], 'store_name': store['store_id__store_name']} for store in user_stores]
        return JsonResponse({'stores': data})
    else:
        return JsonResponse({'error': 'User is not authenticated'}, status=401)
    

@login_required()
def getPOReOrderItemListAPI(request):
    selected_store_id = request.GET.get('store_id')

    stock_data = stock_lists.objects.filter(is_approved=True, store_id=selected_store_id).values('item_id').annotate(
        total_stock_qty=Sum('stock_qty')
    )

    serialized_data = []

    for item in stock_data:
        item_id = item['item_id']

        # Fetch item details
        item_details = items.objects.filter(item_id=item_id).first()

        if item_details:
            # Use the get_available_qty function to calculate the available quantity
            available_qty = get_available_qty(item_id, selected_store_id, item_details.org_id)

            # Check if available_qty is less than re_order_qty
            if item_details.re_order_qty and available_qty < float(item_details.re_order_qty):
                serialized_item = {
                    'item_id': item_details.item_id,
                    'item_no': item_details.item_no,
                    'item_name': item_details.item_name,
                    'type_name': item_details.type_id.type_name,
                    'uom_name': item_details.item_uom_id.item_uom_name,
                    'grandQty': available_qty,
                }

                serialized_data.append(serialized_item)

    # Sort data by available quantity in descending order
    sorted_serialized_data = sorted(serialized_data, key=lambda x: x['grandQty'])

    return JsonResponse({'data': sorted_serialized_data})


# get opening stock list details
@login_required()
def selectPOEntryListDetailsAPI(request):
    if 'selectedItem' not in request.GET:
        return JsonResponse({'error': 'No item selected'}, status=400)

    selected_item_id = request.GET.get('selectedItem')
    
    try:
        selected_item = items.objects.get(item_id=selected_item_id)
        
        # Get the main store
        main_store = store.objects.filter(is_main_store=True).first()

        if not main_store:
            return JsonResponse({'error': 'Main store not found'}, status=404)

        # Calculate available quantity using get_available_qty function
        available_qty = get_available_qty(selected_item_id, main_store.store_id, selected_item.org_id)

        # Prepare item details response
        item_details = {
            'item_id': selected_item.item_id,
            'item_no': selected_item.item_no,
            'type_name': selected_item.type_id.type_name if selected_item.type_id else '',
            'uom_name': selected_item.item_uom_id.item_uom_name if selected_item.item_uom_id else '',
            'grandQty': available_qty,
            'item_name': selected_item.item_name,
        }

        return JsonResponse({'data': [item_details]})
    
    except items.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)



@login_required()
def addPurchaseOrderGenerateAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        data = request.POST
        store_id = data.get("current_store")
        expected_date = data.get('expected_date', None)
        id_org = data.get("org")
        branch_id = data.get("branchs")
        supplier_id = data.get("requisition_to")
        is_credit = data.get('is_credit', False)
        is_cash = data.get('is_cash', False)

        item_ids = request.POST.getlist('item_id[]')
        order_qtys = request.POST.getlist('order_qty[]')
        unit_prices = request.POST.getlist('unit_prices[]')

        try:
            store_instance = store.objects.get(store_id=store_id)
            supplier_instance = suppliers.objects.get(supplier_id=supplier_id)

            with transaction.atomic():
                if id_org and branch_id:
                    try:
                        organization_instance = organizationlst.objects.get(org_id=id_org)
                        branch_instance = branchslist.objects.get(branch_id=branch_id)

                        # Parse expected_date to YYYY-MM-DD format
                        if expected_date and expected_date.strip():  # Check for non-empty string
                            expected_date = datetime.strptime(expected_date, "%Y-%m-%d").date()
                        else:
                            expected_date = None

                        po_generate = purchase_order_list(
                            store_id=store_instance,
                            transaction_date=data['transaction_date'],
                            expected_date=expected_date,
                            is_approved=data['is_approved'],
                            is_approved_by=request.user,
                            approved_date=data['approved_date'],
                            remarks=data['remarks'],
                            id_org=organization_instance,
                            branch_id=branch_instance,
                            supplier_id=supplier_instance,
                            is_credit=is_credit,
                            is_cash=is_cash,
                            dis_percentance=int(data.get("dis_percentance")) if data.get("dis_percentance") else None,
                            vat_percentance=int(data.get("vat_percentance")) if data.get("vat_percentance") else None,
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                        po_generate.save()

                        # Create opening_stockdtl instances for each item
                        for item_id, order_qty, unit_price in zip(item_ids, order_qtys, unit_prices):
                            item_instance = items.objects.get(item_id=item_id)

                            po_Dtl = purchase_orderdtls(
                                order_qty=order_qty,
                                unit_price=unit_price,
                                item_id=item_instance,
                                po_id=po_generate,
                                store_id=store_instance,
                                transaction_date=po_generate.transaction_date,
                                is_approved=po_generate.is_approved,
                                approved_date=po_generate.approved_date,
                                ss_creator=request.user,
                                ss_modifier=request.user,
                            )
                            po_Dtl.save()

                        resp['status'] = 'success'
                        resp['msg'] = 'Purchase order created successfully.'
                    except organizationlst.DoesNotExist:
                        resp['errmsg'] = 'Organization associated with the user does not exist.'
                    except branchslist.DoesNotExist:
                        resp['errmsg'] = 'Branch associated with the user does not exist.'
                else:
                    resp['errmsg'] = 'User is not associated with an organization or branch.'
        except suppliers.DoesNotExist:
            resp['errmsg'] = 'Requisition To Not Selected... Please Select First!..'
        except Exception as e:
            resp['errmsg'] = str(e)
            print("Error:", str(e))

    return JsonResponse(resp)


# edit/update purchase order
@login_required()
def updatePurchaseOrderAPI(request, po_id=None):
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

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
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
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'org_list': org_list,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'purchase_order/edit_purchase_order.html', context)


# proposal report view
@login_required()
def purchaseOrderProposalReportAPI(request, po_id=None):
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

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
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
            })

    context = {
        'item_with_opsDtls': item_with_opsDtls,
        'store_data': store_data,
        'ops_Data': ops_Data,
        'total_grandQty': total_grandQty,
    }

    return render(request, 'purchase_order/po_proposal_report.html', context)



@login_required()
def editUpdatePOManagerAPI(request):
    resp = {'success': False, 'errmsg': ''}
    if request.method == 'POST':
        data = request.POST
        po_id = data.get('po_id')

        if po_id.isnumeric() and int(po_id) > 0:
            id_org = data.get("org")
            branch_id = data.get("branchs")
            if id_org and branch_id:
                try:
                    organization_instance = organizationlst.objects.get(org_id=id_org)
                    branch_instance = branchslist.objects.get(branch_id=branch_id)
                    updatepo_list = purchase_order_list.objects.get(po_id=po_id)
                    # Prevent updates if already approved
                    if updatepo_list.is_approved:
                        return JsonResponse({'success': False, 'errmsg': 'Already Approved!'})

                    with transaction.atomic():
                        # Perform updates
                        store_instance = store.objects.get(store_id=data.get("current_store"))
                        supplier_instance = suppliers.objects.get(supplier_id=data.get("requisition_to"))
                        # Assume organization and branch validation similar to add API
                        
                        # Handling is_credit and is_cash
                        is_credit = data.get("is_credit")
                        is_cash = data.get("is_cash")
                        
                        # Update fields
                        updatepo_list.store_id = store_instance
                        updatepo_list.supplier_id = supplier_instance
                        updatepo_list.id_org=organization_instance
                        updatepo_list.branch_id=branch_instance
                        updatepo_list.transaction_date = data['transaction_date']
                        updatepo_list.expected_date = datetime.strptime(data.get('expected_date', None), "%Y-%m-%d").date() if data.get('expected_date', None) else None
                        updatepo_list.is_approved = data['is_approved']
                        updatepo_list.is_approved_by = request.user
                        updatepo_list.approved_date = data['approved_date']
                        updatepo_list.remarks = data['remarks']
                        updatepo_list.dis_percentance = int(data.get("dis_percentance")) if data.get("dis_percentance") else None
                        updatepo_list.vat_percentance = int(data.get("vat_percentance")) if data.get("vat_percentance") else None
                        updatepo_list.is_credit = is_credit if is_credit else 0
                        updatepo_list.is_cash = is_cash if is_cash else 0
                        updatepo_list.ss_modifier = request.user
                        updatepo_list.save()

                        # Update or Create purchase_orderdtls instances
                        item_ids = request.POST.getlist('item_id[]')
                        order_qtys = request.POST.getlist('order_qty[]')
                        unit_prices = request.POST.getlist('unit_prices[]')

                        for item_id, order_qty, unit_price in zip(item_ids, order_qtys, unit_prices):
                            item_instance = items.objects.get(item_id=item_id)
                            po_Dtl, created = purchase_orderdtls.objects.update_or_create(
                                po_id=updatepo_list,
                                item_id=item_instance,
                                defaults={
                                    'order_qty': order_qty,
                                    'unit_price': unit_price,
                                    'store_id': store_instance,
                                    'transaction_date': updatepo_list.transaction_date,
                                    'is_approved': updatepo_list.is_approved,
                                    'approved_date': updatepo_list.approved_date,
                                    'ss_modifier': request.user,
                                }
                            )

                        resp['success'] = True
                        resp['msg'] = 'Purchase order updated successfully.'
                except Exception as e:
                    resp['errmsg'] = str(e)
            else:
                resp['errmsg'] = 'User is not associated with an organization or branch.'
        else:
            resp['errmsg'] = 'Invalid purchase order ID.'

    return JsonResponse(resp)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def deletePurchaseOrderdtlsItemAPI(request, podtl_id):
    if request.method == 'DELETE':
        try:
            # Delete the purchase_orderdtls instance directly using podtl_id
            purchase_orderdtls.objects.filter(podtl_id=podtl_id).delete()

            return JsonResponse({'success': True, 'msg': f'Successfully deleted'})
        except purchase_orderdtls.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'Purchase Order Details id {podtl_id} not found.'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})