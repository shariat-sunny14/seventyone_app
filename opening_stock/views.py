import sys
import json
from django.core import serializers
from datetime import datetime
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField
from django.db import transaction
from django.db.models import Prefetch
from django.core.paginator import Paginator
from item_setup.models import item_supplierdtl, items
from store_setup.models import store
from organizations.models import branchslist, organizationlst
from django.contrib.auth.decorators import login_required
from stock_list.stock_qty import get_available_qty
from .forms import OpeningStockForm, OpeningStockdtlForm
from . models import opening_stock, opening_stockdtl
from item_pos.models import invoicedtl_list
from stock_list.models import in_stock, stock_lists
from others_setup.models import item_type
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def opening_stockAPI(request):
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

    opStock_list = opening_stock.objects.all()

    op_stockData = {
        'org_list': org_list,
        'opStock_list': opStock_list,
    }
    return render(request, 'opening_stock/opening_stock_list.html', op_stockData)


@login_required()
def getOpeningStockListDetailsAPI(request):
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

    op_data = opening_stock.objects.filter(filter_kwargs)

    data = []

    for op_list in op_data:
        org_name = op_list.id_org.org_name if op_list.id_org else None
        branch_name = op_list.branch_id.branch_name if op_list.branch_id else None
        store_name = op_list.store_id.store_name if op_list.store_id else None
        is_approved_by_first = op_list.is_approved_by.first_name if op_list.is_approved_by is not None else ""
        is_approved_by_last = op_list.is_approved_by.last_name if op_list.is_approved_by is not None else ""
        data.append({
            'op_st_id': op_list.op_st_id,
            'op_no': op_list.op_no,
            'transaction_date': op_list.transaction_date,
            'approved_date': op_list.approved_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'is_approved': op_list.is_approved,
            'is_approved_by_first': is_approved_by_first,
            'is_approved_by_last': is_approved_by_last,
        })

    return JsonResponse({'data': data})


@login_required()
def manage_Opening_StockAPI(request):
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

    return render(request, 'opening_stock/add_opening_stock.html', context)


# get opening stock list
@login_required()
def get_Opening_Stock_listAPI(request):
    selected_type_id = request.GET.get('selectedTypeId')
    selected_id_org = request.GET.get('id_org')
    selected_supplier_id = request.GET.get('filter_suppliers')
    query = request.GET.get('query', '')  # Fetch the query term

    # Base query with filters applied more efficiently
    filters = {'is_active': True}

    if selected_type_id and selected_type_id != '1':
        filters['type_id'] = selected_type_id

    if selected_id_org:
        filters['org_id'] = selected_id_org

    # Fetch the data using select_related and prefetch_related for optimization
    item_data = items.objects.filter(**filters).select_related(
        'org_id', 'type_id'
    ).prefetch_related('item_supplierdtl__supplier_id')

    if selected_supplier_id and selected_supplier_id != '1':
        item_data = item_data.filter(item_supplierdtl__supplier_id=selected_supplier_id)

    # Filter items based on the query (item_name contains query term)
    if query:
        item_data = item_data.filter(Q(item_name__icontains=query) | Q(item_no__icontains=query))

    # Using values to avoid object instantiation
    item_data = item_data.values('item_id', 'item_name')

    # Paginate the results
    paginator = Paginator(item_data, 200)  # 200 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Prepare response
    item_with_grandQty = list(page_obj)  # Convert page_obj to list

    return JsonResponse({'data': item_with_grandQty})


# get opening stock list details
@login_required()
def get_OSItem_details(request, op_st_id=None):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        selected_item_id = request.GET.get('selectedItem')
        selected_id_org = request.GET.get('id_org')

        # Fetch only the main store directly
        main_store = store.objects.filter(is_main_store=True).first()

        if not main_store:
            return JsonResponse({'error': 'Main store not found'}, status=404)

        try:
            # Use select_related to optimize related field fetching (type_id and item_uom_id)
            selected_item = items.objects.select_related('type_id', 'item_uom_id').get(item_id=selected_item_id)

            # Fetch available quantity
            available_qty = get_available_qty(item_id=selected_item, store_id=main_store, org_id=selected_id_org)

            # Prepare item details
            item_details = [{
                'item_id': selected_item.item_id,
                'item_no': selected_item.item_no,
                'type_name': selected_item.type_id.type_name if selected_item.type_id else '',
                'uom_name': selected_item.item_uom_id.item_uom_name if selected_item.item_uom_id else '',
                'sales_price': selected_item.sales_price,
                'grandQty': available_qty,
                'item_name': selected_item.item_name,
            }]

            print("item_details:", item_details)

            return JsonResponse({'data': item_details})

        except items.DoesNotExist:
            return JsonResponse({'error': 'Item not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


# edit/update opening stock
@login_required()
def edit_opening_stockAPI(request, op_st_id=None):
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

    # Get approved without GRN details
    ops_Data = opening_stock.objects.get(pk=op_st_id) if op_st_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = opening_stockdtl.objects.filter(op_st_id=ops_Data).all()

    item_with_opsDtls = []

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        org_instance = ops_Data.id_org if ops_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)

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
        'org_list': org_list,
        'item_with_opsDtls': item_with_opsDtls,
        'ops_Data': ops_Data,
    }

    return render(request, 'opening_stock/edit_opening_stock.html', context)


@login_required()
def exist_openingstockAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST

    store_id = data.get("store_id")
    item_ids = data.getlist('item_ids[]')

    store_instance = store.objects.get(store_id=store_id)

    # Create a list to store error messages for existing items
    existing_items_err_msgs = []

    for item_id in item_ids:
        # Fetch the item associated with the item_id
        item_instance = items.objects.get(item_id=item_id)

        # Check if an item with the same item_id exists in opening_stockdtl
        if opening_stockdtl.objects.filter(Q(item_id=item_instance) & Q(store_id=store_instance)).exists():
            errmsg = f"This Item '{item_instance.item_name}' already exists in this '{store_instance.store_name}' ..."
            existing_items_err_msgs.append(errmsg)

    # Check if there are any existing items
    if existing_items_err_msgs:
        # If there are existing items, return an error response
        resp['msg'] = ', '.join(existing_items_err_msgs)
    else:
        resp['status'] = 'success'

    return JsonResponse(resp)


@login_required()
def Addopening_stock(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST

    store_id = request.POST.get("current_store")
    id_org = data.get("org")
    branch_id = data.get("branchs")
    is_user_id_by = request.POST.get('is_user_id_by')
    item_ids = request.POST.getlist('item_id[]')

    item_qtys = request.POST.getlist('item_qty[]')
    item_batchs = request.POST.getlist('item_batchs[]')
    item_prices = data.getlist('item_price[]')
    item_exp_dates = data.getlist('item_exp_dates[]')
    is_approved = data['is_approved']

    store_instance = store.objects.get(store_id=store_id)

    # Create a list to store error messages for existing items
    existing_items_err_msgs = []

    for item_id in item_ids:
        # Fetch the item associated with the item_id
        item_instance = items.objects.get(item_id=item_id)

        # Check if an item with the same item_id exists in opening_stockdtl
        if opening_stockdtl.objects.filter(Q(item_id=item_instance) & Q(store_id=store_instance)).exists():
            errmsg = f"This Item '{item_instance.item_name}' already exists in this '{store_instance.store_name}' ..."
            existing_items_err_msgs.append(errmsg)

    # Check if there are any existing items
    if existing_items_err_msgs:
        # If there are existing items, return an error response
        return JsonResponse({'success': False, 'errmsg': ', '.join(existing_items_err_msgs)})

    else:
        try:
            with transaction.atomic():
                try:
                    # Check if the user exists
                    user_instance = None
                    if is_user_id_by:
                        user_instance = User.objects.get(user_id=is_user_id_by)
                except User.DoesNotExist:
                    return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)
                
                if id_org and branch_id:
                    try:
                        organization_instance = organizationlst.objects.get(org_id=id_org)
                        branch_instance = branchslist.objects.get(branch_id=branch_id)
                        # Create an opening_stock instance
                        openingStock = opening_stock(
                            store_id=store_instance,
                            transaction_date=data['transaction_date'],
                            is_approved=is_approved,
                            is_approved_by=user_instance,
                            approved_date=data['approved_date'],
                            remarks=data['remarks'],
                            id_org=organization_instance,
                            branch_id=branch_instance,
                            ss_creator=request.user,
                        )
                        openingStock.save()

                        # Create opening_stockdtl instances for each item
                        for item_id, item_price, qty, batch, exp_dates in zip(item_ids, item_prices, item_qtys, item_batchs, item_exp_dates):
                            item_instance = items.objects.get(item_id=item_id)

                            # Handle null or empty expiration dates
                            if exp_dates in [None, '']:
                                exp_dates = None  # Set to None for empty values

                            openingStockDtl = opening_stockdtl(
                                op_item_qty=qty,
                                unit_price=item_price,
                                item_batch=batch,
                                item_exp_date=exp_dates,
                                item_id=item_instance,
                                op_st_id=openingStock,
                                store_id=store_instance,
                                opening_date=openingStock.transaction_date,
                                is_approved=openingStock.is_approved,
                                approved_date=openingStock.approved_date,
                                ss_creator=request.user
                            )
                            openingStockDtl.save()

                            stock_data = stock_lists(
                                op_st_id=openingStock,
                                op_stdtl_id=openingStockDtl,
                                stock_qty=qty,
                                item_batch=batch,
                                item_exp_date=exp_dates,
                                recon_type=True, #recon_type=True is adding item in stock list
                                item_id=item_instance,
                                store_id=store_instance,
                                is_approved=openingStock.is_approved,
                                approved_date=openingStock.approved_date,
                                ss_creator=request.user
                            )
                            stock_data.save()

                            # Check if item and store combination exists in in_stock
                            approved_status = openingStock.is_approved

                            if approved_status == '1':
                                in_stock_obj, created = in_stock.objects.get_or_create(
                                    item_id=item_instance,
                                    store_id=store_instance,
                                    defaults={
                                        'stock_qty': qty,
                                    }
                                )
                                if not created:
                                    # If the record exists, update the stock_qty
                                    in_stock_obj.stock_qty += float(qty)
                                    in_stock_obj.save()

                        resp['status'] = 'success'
                        return JsonResponse({'success': True, 'msg': 'Successful'})
                    except organizationlst.DoesNotExist:
                        resp['errmsg'] = 'Organization associated with the user does not exist.'
                    except branchslist.DoesNotExist:
                        resp['errmsg'] = 'Branch associated with the user does not exist.'
                else:
                    resp['errmsg'] = 'User is not associated with an organization or branch.'
        except Exception as e:
            print("Error:", str(e))
            resp['status'] = 'failed'

    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required()
def editUpdate_openingStockAPI(request):
    resp = {'success': False, 'errmsg': ''}
    data = request.POST

    op_st_id = data.get('op_st_id')

    if op_st_id.isnumeric() and int(op_st_id) > 0:
        id_org = data.get("org")
        branch_id = data.get("branchs")
        store_id = data.get("current_store")
        item_ids = data.getlist('item_id[]')
        item_qtys = data.getlist('item_qty[]')
        item_batchs = data.getlist('item_batchs[]')
        item_prices = data.getlist('item_price[]')
        item_exp_dates = data.getlist('item_exp_dates[]')
        is_approved_by_user = data.get('is_user_id_by')
        is_approved = data['is_approved']

        try:
            # Check if the user exists
            user_instance = None
            if is_approved_by_user:
                user_instance = User.objects.get(user_id=is_approved_by_user)
        except User.DoesNotExist:
            return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)

        org_instance = organizationlst.objects.get(org_id=id_org)
        branch_instance = branchslist.objects.get(branch_id=branch_id)
        store_instance = store.objects.get(store_id=store_id)
        openingStock = opening_stock.objects.get(op_st_id=op_st_id)

        for item_id in item_ids:
            # Fetch the item associated with the item_id
            item_value = items.objects.get(item_id=item_id, org_id=org_instance)

            # Check if the same combination of item_id, store_id,  in opening_stockdtl for another op_st_id
            existing_items = opening_stockdtl.objects.filter(
                Q(item_id=item_value) & Q(store_id=store_instance)
            ).exclude(op_st_id=openingStock)

            if existing_items.exists():
                errmsg = f"This Item: '{item_value.item_name}' is already exists in this '{store_instance.store_name} ...'"
                return JsonResponse({'success': False, 'errmsg': errmsg})

    # If it's already approved
    if openingStock.is_approved:
        return JsonResponse({'success': False, 'errmsg': 'Already Approved!'})

    try:
        with transaction.atomic():
            # Update the without_GRN instance
            openingStock.id_org = org_instance
            openingStock.branch_id = branch_instance
            openingStock.store_id = store_instance
            openingStock.is_approved = is_approved
            openingStock.is_approved_by = user_instance
            openingStock.approved_date = data['approved_date']
            openingStock.remarks = data['remarks']
            openingStock.ss_modifier = request.user
            openingStock.save()

            # Update or create without_GRNdtl instances for each item
            for item_id, item_price, qty, batch, exp_dates in zip(item_ids, item_prices, item_qtys, item_batchs, item_exp_dates):
                item_instance = items.objects.get(item_id=item_id)

                # Handle null or empty expiration dates
                if exp_dates in [None, '']:
                    exp_dates = None  # Set to None for empty values

                openingStockkDtl, created = opening_stockdtl.objects.update_or_create(
                    op_st_id=openingStock,
                    item_id=item_instance,
                    defaults={
                        'op_item_qty': qty,
                        'unit_price': item_price,
                        'item_batch': batch,
                        'item_exp_date': exp_dates,
                        'store_id': store_instance,
                        'is_approved': openingStock.is_approved,
                        'approved_date': openingStock.approved_date,
                        'ss_modifier': request.user,
                    }
                )

                # Save the without_GRNdtl instance
                openingStockkDtl.save()

                # Update or create stock_lists
                stock_data, created = stock_lists.objects.update_or_create(
                    op_st_id=openingStock,
                    op_stdtl_id=openingStockkDtl,
                    item_id=item_instance,
                    defaults={
                        'stock_qty': qty,
                        'item_batch': batch,
                        'item_exp_date': exp_dates,
                        'store_id': store_instance,
                        'recon_type': True, #recon_type=True is adding item in stock list
                        'is_approved': openingStock.is_approved,
                        'approved_date': openingStock.approved_date,
                        'ss_modifier': request.user
                    }
                )
                # Save the in_stock instance
                stock_data.save()

                # Check if item and store combination exists in in_stock
                approved_status = openingStock.is_approved

                if approved_status == '1':
                    in_stock_obj, created = in_stock.objects.get_or_create(
                        item_id=item_instance,
                        store_id=store_instance,
                        defaults={
                            'stock_qty': qty,
                        }
                    )
                    if not created:
                        # If the record exists, update the stock_qty
                        in_stock_obj.stock_qty += float(qty)
                        in_stock_obj.save()

            resp['success'] = True
            return JsonResponse({'success': True, 'msg': 'Successful'})
    except Exception as e:
        print("Error:", str(e))
        resp['errmsg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")


# edit/update opening stock
@login_required()
def reportOpeningStockAPI(request, op_st_id=None):
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

    # Get approved without GRN details
    ops_Data = opening_stock.objects.get(pk=op_st_id) if op_st_id else None

    # Query without_GRNdtl records related to the withgrnData
    opsdtl_data = opening_stockdtl.objects.filter(op_st_id=ops_Data).all()

    item_with_opsDtls = []

    for item in item_data:
        store_instance = ops_Data.store_id if ops_Data else None
        org_instance = ops_Data.id_org if ops_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)

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
        'org_list': org_list,
        'item_with_opsDtls': item_with_opsDtls,
        'ops_Data': ops_Data,
    }

    return render(request, 'opening_stock/report_opening_stock.html', context)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def delete_ops_dtls(request, op_stdtl_id):
    if request.method == 'DELETE':
        try:
            # Get the opening_stockdtl instance using op_stdtl_id
            ops_dtlsID = opening_stockdtl.objects.get(op_stdtl_id=op_stdtl_id)
            # Get all stock_list entries related to this ops_dtlsID
            stock_data = stock_lists.objects.filter(op_stdtl_id=ops_dtlsID)
            # Delete the stock_list entries
            stock_data.delete()

            # Finally, delete the opening_stockdtl entry
            ops_dtlsID.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        except opening_stockdtl.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'opening_stockdtl id {op_stdtl_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Error occurred while deleting: {str(e)}'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})
