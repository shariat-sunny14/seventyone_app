import sys
import json
from django.db.models import Q, F, Sum, Prefetch, ExpressionWrapper, fields, FloatField
from django.db import transaction
from datetime import datetime
from django.core import serializers
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.serializers import serialize
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from others_setup.models import item_type
from store_setup.models import store
from organizations.models import branchslist, organizationlst
from item_setup.models import item_supplierdtl, items
from stock_list.models import in_stock, stock_lists
from po_return_receive.models import po_return_received_details
from stock_list.stock_qty import get_available_qty
from stock_reconciliation.models import item_reconciliation, item_reconciliationdtl
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def stockReconciliationManagerAPI(request):
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

    return render(request, 'stock_reconciliation/stock_reconciliation.html', context)


@login_required()
def getReconciliationItemListAPI(request):
    selected_store_id = request.GET.get('store_id')
    filter_org = request.GET.get('org_id')
    search_query = request.GET.get('query', '')  # Get the search query
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 100))  # Default page size is 100

    try:
        # Fetch stock information related to the selected store
        stock_qs = in_stock.objects.filter(store_id=selected_store_id).select_related('store_id').only(
            'store_id', 'store_id__store_name', 'stock_qty'
        )

        # Build the base query for filtering items
        search_filters = Q(item_name__icontains=search_query) | Q(item_no__icontains=search_query)

        item_data_query = items.objects.filter(
            Q(is_active=True),
            Q(org_id=filter_org),
            search_filters,
        ).select_related('type_id', 'item_uom_id').only(
            'item_id', 'item_no', 'item_name', 'sales_price', 'type_id__type_name', 'item_uom_id__item_uom_name'
        ).prefetch_related(
            Prefetch('item_id2in_stock', queryset=stock_qs, to_attr='prefetched_stock')
        )

        # Paginate the query
        paginator = Paginator(item_data_query, page_size)
        page_obj = paginator.get_page(page_number)

        # Build the serialized response
        serialized_data = []
        for item in page_obj:
            available_qty = get_available_qty(item.item_id, selected_store_id, filter_org)
            stock_details = item.prefetched_stock[0] if item.prefetched_stock else None

            serialized_item = {
                'item_id': item.item_id,
                'item_no': item.item_no,
                'item_name': item.item_name,
                'item_type_name': item.type_id.type_name if item.type_id else "Unknown",
                'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else "Unknown",
                'item_Supplier': item.supplier_id.supplier_name if item.supplier_id else "Unknown",
                'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
                'item_price': item.sales_price,
                'stock_qty': available_qty,
            }

            serialized_data.append(serialized_item)

        # Sort by stock quantity in descending order
        sorted_serialized_data = sorted(serialized_data, key=lambda x: x['stock_qty'], reverse=True)

        response_data = {
            'data': sorted_serialized_data,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'total_items': paginator.count,
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@login_required()
def selectReconciliationItemAPI(request):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        store_id = request.GET.get('store_id')
        selected_stock_id = request.GET.get('selectedItem')
        filter_org = request.GET.get('org_id')

        try:
            get_itemID = items.objects.get(item_id=selected_stock_id, org_id=filter_org)
            stock_data = in_stock.objects.filter(item_id=get_itemID, store_id=store_id).values('item_id', 'stock_qty')
            
            for item in stock_data:
                item_id = item['item_id']

                available_qty = get_available_qty(item_id, store_id, filter_org)
                
                item_id = get_itemID.item_id
                item_type_name = get_itemID.type_id.type_name

                supplier_data = item_supplierdtl.objects.filter(item_id=item_id).first()

                

                stock_details = in_stock.objects.filter(item_id=item_id, store_id=store_id).first()
                store = stock_details.store_id
                item_Supplier = supplier_data.supplier_id.supplier_name if supplier_data else None
                store_info = {
                    'store_id': store.store_id,
                    'store_name': store.store_name
                }

                
                sales_price = get_itemID.sales_price

                item_info = {
                    'store_id': store_info['store_id'],
                    'store_name': store_info['store_name'],
                    'item_id': item_id,
                    'item_name': get_itemID.item_name,
                    'item_no': get_itemID.item_no,
                    'item_type_name': item_type_name,
                    'stock_qty': available_qty,
                    'item_price': sales_price,
                    'item_Supplier': item_Supplier,
                }

                return JsonResponse({'data': [item_info]})
            else:
                return JsonResponse({'data': []})
        except stock_lists.DoesNotExist:
            return JsonResponse({'error': 'Stock ID does not exist'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required()
def getReconciliationItemAPI(request):
    option = request.GET.get('option')
    search_query = request.GET.get('search_query', '')
    org_id_filter = request.GET.get('org_filter')
    branchs_filter = request.GET.get('branchs_filter')
    store_filter = request.GET.get('store_filter')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if search_query is not empty
    if search_query:
        filter_kwargs |= Q(description__icontains=search_query) | Q(recon_no__icontains=search_query)

    # Add org_id filter conditions
    if org_id_filter:
        filter_kwargs &= Q(id_org_id=org_id_filter)
    
    # Add branch_id filter condition
    if branchs_filter:
        filter_kwargs &= Q(branch_id_id=branchs_filter)

    # Add store_id filter condition
    if store_filter:
        filter_kwargs &= Q(store_id_id=store_filter)

    # Add is_approved filter condition based on the option
    if option == 'true':
        filter_kwargs &= Q(is_approved=True)
    elif option == 'false':
        filter_kwargs &= Q(is_approved=False)

    # Add date range filtering if from_date and to_date are provided
    if from_date:
        filter_kwargs &= Q(recon_date__gte=datetime.strptime(from_date, "%Y-%m-%d"))
    if to_date:
        filter_kwargs &= Q(recon_date__lte=datetime.strptime(to_date, "%Y-%m-%d"))

    # Filter the items directly and retrieve values
    items_data = item_reconciliation.objects.filter(filter_kwargs).values(
        'recon_id', 'recon_no', 'recon_date', 'is_approved', 'id_org__org_name', 'branch_id__branch_name', 'store_id__store_name'
    )

    return JsonResponse({
        'data': list(items_data),  # Convert QuerySet to list for JSON serialization
    })


@login_required()
def showReconciliationItemDetailsAPI(request):
    recon_id = request.GET.get('recon_id')
    org_id = request.GET.get('org_id')
    store_id = request.GET.get('store_id')

    if not recon_id:
        return JsonResponse({'error': 'Missing recon_id parameter'}, status=400)
    
    try:
        # Fetch the reconciliation instance
        reconciliation = item_reconciliation.objects.get(recon_id=recon_id)
    except item_reconciliation.DoesNotExist:
        return JsonResponse({'error': 'Reconciliation not found'}, status=404)
    
    try:
        # Fetch the organization instance
        org_instance = organizationlst.objects.get(org_id=org_id)
    except organizationlst.DoesNotExist:
        return JsonResponse({'error': 'Organization does not exist'}, status=404)
    
    try:
        # Fetch the store instance
        store_instance = store.objects.get(store_id=store_id)
    except store.DoesNotExist:
        return JsonResponse({'error': 'Store does not exist'}, status=404)

    try:
        # Fetch all item details related to the given recon_id
        items_data = item_reconciliationdtl.objects.filter(recon_id=recon_id).select_related('item_id')
        
        item_list = []
        for item in items_data:
            if isinstance(item.item_id, items):
                available_qty = get_available_qty(item_id=item.item_id.item_id, store_id=store_instance.store_id, org_id=org_instance.org_id)
                
                item_list.append({
                    'recondtl_id': item.recondtl_id,
                    'item_id': item.item_id.item_id,
                    'item_no': item.item_id.item_no,
                    'item_name': item.item_id.item_name,
                    'item_type': item.item_id.type_id.type_name if item.item_id.type_id else '',
                    'item_supplier': item.item_id.supplier_id.supplier_name if item.item_id.supplier_id else '',
                    'stock_qty': available_qty,
                    'recon_qty': item.recon_qty,
                    'item_price': item.unit_price,
                })
            else:
                return JsonResponse({'error': f'Invalid item instance for item_id: {item.item_id}'}, status=400)

        # Construct the response with necessary fields
        response_data = {
            'org_id': reconciliation.id_org.org_id if reconciliation.id_org else None,
            'branch_id': reconciliation.branch_id.branch_id if reconciliation.branch_id else None,
            'is_approved': reconciliation.is_approved,
            'recon_no': reconciliation.recon_no,
            'store_id': reconciliation.store_id.store_id if reconciliation.store_id else None,
            'recon_type': reconciliation.recon_type,
            'description': reconciliation.description,
            'items': item_list,
        }

        return JsonResponse(response_data)
    
    except item_reconciliationdtl.DoesNotExist:
        return JsonResponse({'error': 'No items found for the given recon_id'}, status=404)
    

@login_required()
def saveReconsalationManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Submission Failed'}
    data = request.POST
    recon_id = data.get('recon_id')
    org_id = data.get('org_select')
    branch_id = data.get('branchs')
    store_id = data.get('store_value')
    recon_types = data.get('recon_type')
    description = data.get('description')
    is_approved = data.get('is_approved', False)

    try:
        with transaction.atomic():
            # Fetch instances of the foreign key objects
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            store_instance = store.objects.get(store_id=store_id)

            if recon_id:  # If recon_id is provided, try to fetch the existing record
                try:
                    reconciliation = item_reconciliation.objects.get(recon_id=recon_id)

                    # If it's already approved
                    if reconciliation.is_approved:
                        return JsonResponse({'success': False, 'errmsg': 'Already Approved!'})
    
                    reconciliation.id_org = organization_instance
                    reconciliation.branch_id = branch_instance
                    reconciliation.store_id = store_instance
                    reconciliation.recon_type = recon_types
                    reconciliation.description = description
                    reconciliation.is_approved = is_approved

                    # Conditionally set is_approved_by and approved_date only if approved
                    if is_approved:
                        reconciliation.is_approved_by = request.user
                        reconciliation.approved_date = datetime.now()

                    reconciliation.ss_modifier = request.user
                    reconciliation.save()

                except item_reconciliation.DoesNotExist:
                    resp['errmsg'] = f"Reconciliation with id {recon_id} does not exist."
                    return JsonResponse(resp)
            else:  # If recon_id is not provided, create a new record
                reconciliation = item_reconciliation(
                    id_org=organization_instance,
                    branch_id=branch_instance,
                    store_id=store_instance,
                    recon_type=recon_types,
                    description=description,
                    is_approved=is_approved,
                    ss_creator=request.user,
                )

                # Conditionally set is_approved_by and approved_date only if approved
                if is_approved:
                    reconciliation.is_approved_by = request.user
                    reconciliation.approved_date = datetime.now()

                reconciliation.save()

            # Handle item details
            item_data = list(zip(
                request.POST.getlist('item_id[]'),
                request.POST.getlist('recon_stockQty[]'),
                request.POST.getlist('item_price[]'),
            ))

            for item_id, qty, price in item_data:
                item_instance = items.objects.get(item_id=item_id)

                # Handle item_reconciliation_dtl creation or updating
                if recon_id:
                    try:
                        item_reconciliation_dtl = item_reconciliationdtl.objects.get(
                            recon_id=reconciliation, item_id=item_instance)
                        item_reconciliation_dtl.recon_qty = qty
                        item_reconciliation_dtl.unit_price = price
                        item_reconciliation_dtl.is_approved = is_approved
                        item_reconciliation_dtl.approved_date = datetime.now() if is_approved else None
                        item_reconciliation_dtl.ss_modifier = request.user
                        item_reconciliation_dtl.save()
                    except item_reconciliationdtl.DoesNotExist:
                        item_reconciliation_dtl = item_reconciliationdtl.objects.create(
                            recon_id=reconciliation,
                            item_id=item_instance,
                            store_id=store_instance,
                            recon_qty=qty,
                            unit_price=price,
                            recondtl_date=datetime.now(),
                            is_approved=is_approved,
                            approved_date=datetime.now() if is_approved else None,
                            ss_creator=request.user,
                        )
                else:
                    item_reconciliation_dtl = item_reconciliationdtl.objects.create(
                        recon_id=reconciliation,
                        item_id=item_instance,
                        store_id=store_instance,
                        recon_qty=qty,
                        unit_price=price,
                        recondtl_date=datetime.now(),
                        is_approved=is_approved,
                        approved_date=datetime.now() if is_approved else None,
                        ss_creator=request.user,
                    )

                # Handle stock_lists creation or updating
                stock_data, created = stock_lists.objects.get_or_create(
                    recon_id=reconciliation,
                    recondtl_id=item_reconciliation_dtl,
                    item_id=item_instance,
                    store_id=store_instance,
                    defaults={
                        'stock_qty': qty,
                        'recon_type': False,  # recon_type=False, cause this stock list another module no need to effect
                        'is_approved': is_approved,
                        'approved_date': datetime.now().date() if is_approved else None,
                        'ss_creator': request.user,
                    }
                )
                if not created:
                    stock_data.stock_qty = qty
                    stock_data.is_approved = is_approved
                    stock_data.approved_date = datetime.now().date() if is_approved else None
                    stock_data.ss_modifier = request.user
                    stock_data.save()

                # Update stock quantities if reconciliation is approved
                if is_approved:
                    in_stock_obj, _ = in_stock.objects.get_or_create(
                        item_id=item_instance,
                        store_id=store_instance,
                        defaults={'stock_qty': 0}  # Set default stock_qty to 0
                    )
                    if recon_types == "1":
                        in_stock_obj.stock_qty += float(qty)
                    elif recon_types in ("2", "3", "4"):
                        in_stock_obj.stock_qty -= float(qty)
                    in_stock_obj.save()

            resp = {'status': 'success', 'msg': 'Saved successfully', 'recon_id': reconciliation.recon_id}

    except organizationlst.DoesNotExist:
        resp['errmsg'] = f"Organization with id {org_id} does not exist."
    except branchslist.DoesNotExist:
        resp['errmsg'] = f"Branch with id {branch_id} does not exist."
    except store.DoesNotExist:
        resp['errmsg'] = f"Store with id {store_id} does not exist."
    except items.DoesNotExist:
        resp['errmsg'] = f"Item with id {item_id} does not exist."
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def deleteReconciliationDtls(request, recondtl_id):
    if request.method == 'DELETE':
        try:
            # Get the item_reconciliationdtl instance using recondtl_id
            recon_DtlID = item_reconciliationdtl.objects.get(recondtl_id=recondtl_id)
            # If it's already approved
            if recon_DtlID.is_approved:
                return JsonResponse({'success': False, 'errmsg': 'This Reconciliation is Approved. Delete Not Allow!'})
            # Get all stock_list entries related to this recon_DtlID
            stock_value = stock_lists.objects.filter(recondtl_id=recon_DtlID)
            # Delete the stock_list entries
            stock_value.delete()
            # Finally, delete the item_reconciliationdtl entry
            recon_DtlID.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        except item_reconciliationdtl.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'item reconciliation dtl id {recondtl_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Error occurred while deleting: {str(e)}'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})