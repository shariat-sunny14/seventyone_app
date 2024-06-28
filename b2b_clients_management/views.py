import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from item_setup.models import items
from department.models import departmentlst
from . models import b2b_client_item_rates, b2b_client_item_percentage, b2b_client_dept_percentage
from supplier_setup.models import suppliers
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def b2bClientsManagementAPI(request):
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

    return render(request, 'b2b_clients/b2b_clients_percent.html', context)


@login_required()
def b2bCRateSetupManagementAPI(request):
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

    return render(request, 'b2b_clients/b2b_clients_item_rate.html', context)

# for b2b_clients_percent
@login_required()
def getOrgWiseFilterateItemsAPI(request):
    filter_org_id = request.GET.get('filter_org')
    search_query = request.GET.get('search_query', '').strip()

    # Start with all items or filter by organization if org_id is provided
    filtered_items = items.objects.filter(is_active=True)  # Initialize filtered_items

    if filter_org_id:
        filtered_items = filtered_items.filter(org_id=filter_org_id)

    # Filter further by search query on item number or item name
    if search_query:
        filtered_items = filtered_items.filter(
            Q(item_no__icontains=search_query) |
            Q(item_name__icontains=search_query)
        )

    # Build the data list to return as JSON
    data = [
        {
            'item_id': item.item_id,
            'item_no': item.item_no,
            'item_name': item.item_name,
        }
        for item in filtered_items
    ]

    return JsonResponse(data, safe=False)


# for b2b_clients items_percentage_amt get
@login_required()
def fetchItemsPercentageAmtAPI(request):
    org_filter = request.GET.get('org_filter')
    item_ids = request.GET.getlist('items_id[]')
    supplier_ids = request.GET.get('suppliers_id')

    # Start with all items percentage data or filter by organization if org_filter is provided
    filtered_items_percentage = b2b_client_item_percentage.objects.all()

    if org_filter:
        filtered_items_percentage = filtered_items_percentage.filter(org_id=org_filter)

    # Filter further by item_ids
    if item_ids:
        filtered_items_percentage = filtered_items_percentage.filter(item_id__in=item_ids)

    # Filter further by supplier_ids
    if supplier_ids:
        filtered_items_percentage = filtered_items_percentage.filter(supplier_id=supplier_ids)

    # Construct a list of dictionaries containing the required fields
    data = []
    for item in filtered_items_percentage:
        data.append({
            'item_per_id': item.item_per_id,
            'item_id': item.item_id.item_id,
            'b2b_item_perc': item.b2b_item_perc,
            'b2b_item_amt': item.b2b_item_amt,
        })

    # Return the data list as JSON
    return JsonResponse(data, safe=False)


# for b2b_clients departmenr_percentage_amt get
@login_required()
def fetchDeptsPercentageAmtAPI(request):
    org_filter = request.GET.get('org_filter')
    dept_ids = request.GET.getlist('dept_id[]')
    supplier_ids = request.GET.get('suppliers_id')

    # Start with all items percentage data or filter by organization if org_filter is provided
    filtered_depts_percentage = b2b_client_dept_percentage.objects.all()

    if org_filter:
        filtered_depts_percentage = filtered_depts_percentage.filter(org_id=org_filter)

    # Filter further by dept_ids
    if dept_ids:
        filtered_depts_percentage = filtered_depts_percentage.filter(dept_id__in=dept_ids)

    # Filter further by supplier_ids
    if supplier_ids:
        filtered_depts_percentage = filtered_depts_percentage.filter(supplier_id=supplier_ids)

    # Construct a list of dictionaries containing the required fields
    data = []
    for dept in filtered_depts_percentage:
        data.append({
            'dept_per_id': dept.dept_per_id,
            'dept_id': dept.dept_id.dept_id,
            'b2b_dept_perc': dept.b2b_dept_perc,
            'b2b_dept_amt': dept.b2b_dept_amt,
        })

    # Return the data list as JSON
    return JsonResponse(data, safe=False)


@login_required()
def getOrgWiseFilterateDeptsAPI(request):
    filter_org_id = request.GET.get('filter_org')
    search_query = request.GET.get('search_query', '').strip()

    # Start with all departmentlst or filter by organization if org_id is provided
    if filter_org_id:
        filtered_depts = departmentlst.objects.filter(is_active=True, is_parent_dept=False, id_org=filter_org_id)

    # Filter further by search query on item number or item name
    if search_query:
        filtered_depts = filtered_depts.filter(
            Q(dept_no__icontains=search_query) | 
            Q(dept_name__icontains=search_query)
        )

    # Build the data list to return as JSON
    data = [
        {
            'dept_id': dept.dept_id,
            'dept_no': dept.dept_no,
            'dept_name': dept.dept_name,
            'phone': dept.phone,
            'hotline': dept.hotline
        }
        for dept in filtered_depts
    ]

    return JsonResponse(data, safe=False)


# for b2b_clients_item_rate
@login_required()
def getListOfClientsItemRateAPI(request):
    filter_org_id = request.GET.get('org_filter')
    search_query = request.GET.get('item_search_query', '').strip()

    # Start with all items or filter by organization if org_id is provided
    filtered_items = items.objects.filter(is_active=True)  # Initialize filtered_items

    if filter_org_id:
        filtered_items = filtered_items.filter(org_id=filter_org_id)

    # Filter further by search query on item number or item name
    if search_query:
        filtered_items = filtered_items.filter(
            Q(item_no__icontains=search_query) | 
            Q(item_name__icontains=search_query)
        )

    # Build the data list to return as JSON
    data = [
        {
            'item_id': item.item_id,
            'item_no': item.item_no,
            'item_name': item.item_name,
        }
        for item in filtered_items
    ]

    return JsonResponse(data, safe=False)


# get item id wise org and supplier wise b2b_client_rate
@login_required()
def getItemListWiseB2bClientItemRateAPI(request, item_id):
    org_id = request.GET.get('filter_org')
    supplier_id = request.GET.get('supplier_id')
    print("Org ID:", org_id)
    print("Supplier ID:", supplier_id)

    try:
        org_instance = organizationlst.objects.get(org_id=org_id)
        supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
    except organizationlst.DoesNotExist:
        return JsonResponse({'error': 'Organization does not exist.'}, status=404)
    except suppliers.DoesNotExist:
        return JsonResponse({'error': 'Supplier does not exist.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    try:
        item_instance = get_object_or_404(items, item_id=item_id)

        b2bccli_item_rateDtls = b2b_client_item_rates.objects.filter(item_id=item_instance, org_id=org_instance, supplier_id=supplier_instance)
        
        b2bitem_dtls = []

        for rate_detail in b2bccli_item_rateDtls:
            b2bitem_dtls.append({
                'b2b_clitr_id': rate_detail.b2b_clitr_id,
                'b2b_client_rate': rate_detail.b2b_client_rate,
            })

        context = {
            'b2bitem_dtls': b2bitem_dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# 
@login_required()
def addUpdateB2bDeptItemPercentageAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('filter_org')
    supplier_id = data.get('supplier_id')
    item_ids = data.getlist('item_ids[]')
    item_pers = data.getlist('item_pers[]')
    item_amts = data.getlist('item_amts[]')
    dept_ids = data.getlist('dept_ids[]')
    dept_pers = data.getlist('dept_pers[]')
    dept_amts = data.getlist('dept_amts[]')

    try:
        org_instance = organizationlst.objects.get(org_id=int(org_id))
        supplier_instance = suppliers.objects.get(supplier_id=int(supplier_id))
    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'errmsg': 'Organization does not exist'})

    try:
        with transaction.atomic():
            # for items
            for item_id, item_per, item_amt in zip(item_ids, item_pers, item_amts):
                try:
                    item_instance = items.objects.get(item_id=int(item_id))
                except ObjectDoesNotExist:
                    return JsonResponse({'success': False, 'errmsg': f'Item with ID {item_id} does not exist'})

                # Ensure item_per and item_amt are converted to integers
                item_per_int = int(item_per) if item_per.strip() else 0
                item_amt_int = int(item_amt) if item_amt.strip() else 0

                if item_per_int > 0 or item_amt_int > 0:
                    # Create or update b2b_client_item_percentage instance
                    b2b_item_instance, created = b2b_client_item_percentage.objects.update_or_create(
                        org_id=org_instance,
                        supplier_id=supplier_instance,
                        item_id=item_instance,
                        defaults={
                            'b2b_item_perc': item_per_int,
                            'b2b_item_amt': item_amt_int,
                        }
                    )

            # for departments
            for dept_id, dept_per, dept_amt in zip(dept_ids, dept_pers, dept_amts):
                try:
                    dept_instance = departmentlst.objects.get(dept_id=int(dept_id))
                except ObjectDoesNotExist:
                    return JsonResponse({'success': False, 'errmsg': f'Item with ID {item_id} does not exist'})

                # Ensure dept_per and dept_amt are converted to integers
                dept_per_int = int(dept_per) if dept_per.strip() else 0
                dept_amt_int = int(dept_amt) if dept_amt.strip() else 0

                if dept_per_int > 0 or dept_amt_int > 0:
                    # Create or update b2b_client_item_percentage instance
                    b2b_dept_instance, created = b2b_client_dept_percentage.objects.update_or_create(
                        org_id=org_instance,
                        supplier_id=supplier_instance,
                        dept_id=dept_instance,
                        defaults={
                            'b2b_dept_perc': dept_per_int,
                            'b2b_dept_amt': dept_amt_int,
                        }
                    )
            resp = {'success': True, 'msg': 'saved successfully'}
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


# save or update b2b_client_item_rate
@login_required()
def saveUpdateB2bClientItemRateAPI(request):
    if request.method == 'POST':
        org_id = request.POST.get('filter_org')
        item_id = request.POST.get('item_id')
        supplier_id = request.POST.get('supplier_id')
        b2b_client_rate = request.POST.get('b2b_client_rate')
        b2b_clitr_id = request.POST.get('b2b_clitr_id')  # Get the b2b_clitr_id from the request

        try:
            org_instance = organizationlst.objects.get(org_id=org_id)
            item_instance = items.objects.get(item_id=item_id)
            supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
        except organizationlst.DoesNotExist:
            return JsonResponse({'error': 'Organization does not exist.'}, status=404)
        except items.DoesNotExist:
            return JsonResponse({'error': 'Item does not exist.'}, status=404)
        except suppliers.DoesNotExist:
            return JsonResponse({'error': 'Supplier does not exist.'}, status=404)

        # If b2b_clitr_id is provided, update the existing record
        if b2b_clitr_id:
            try:
                b2b_client_rate_obj = b2b_client_item_rates.objects.get(b2b_clitr_id=b2b_clitr_id)
                b2b_client_rate_obj.b2b_client_rate = b2b_client_rate
                b2b_client_rate_obj.ss_modifier = request.user
                b2b_client_rate_obj.save()
                return JsonResponse({'success': True, 'msg': 'B2B client item rate updated successfully.'})
            except b2b_client_item_rates.DoesNotExist:
                return JsonResponse({'error': 'B2B client item rate with the provided ID does not exist.'}, status=404)

        # Otherwise, create a new record or update an existing one
        else:
            b2b_client_rate_obj, created = b2b_client_item_rates.objects.get_or_create(
                org_id=org_instance,
                item_id=item_instance,
                supplier_id=supplier_instance,
                defaults={'b2b_client_rate': b2b_client_rate}
            )

            if created:
                b2b_client_rate_obj.ss_creator = request.user

            b2b_client_rate_obj.ss_modifier = request.user
            b2b_client_rate_obj.b2b_client_rate = b2b_client_rate
            b2b_client_rate_obj.save()

            return JsonResponse({'success': True, 'msg': 'B2B client item rate updated successfully.'})

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@login_required()
def getB2bClientsListManagerAPI(request):
    supp_search_query = request.GET.get('supp_search_query', '')
    org_id_wise_filter = request.GET.get('org_filter', '')

    # Initialize an empty Q object for dynamic filters
    filter_kwargs = Q()

    # Add search conditions only if supp_search_query is not empty
    if supp_search_query:
        filter_kwargs |= Q(supplier_name__icontains=supp_search_query) | Q(supplier_no__icontains=supp_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Include the static flags in the filter
    static_filters = Q(b2bclient_flag=4)

    # Combine static filters with dynamic filters
    combined_filters = static_filters & filter_kwargs

    # Apply combined_filters to the query
    supp_data = suppliers.objects.filter(is_active=True).filter(combined_filters)

    data = []
    for supp_item in supp_data:
        data.append({
            'supplier_id': supp_item.supplier_id,
            'supplier_no': supp_item.supplier_no,
            'supplier_name': supp_item.supplier_name,
        })

    return JsonResponse({'data': data})