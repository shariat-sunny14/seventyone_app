from django.db.models import Q
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from organizations.models import branchslist, organizationlst
from setup_modes.models import UItemplate_setup
from .forms import storeSetupForm, storeUpdateSetupForm
from .models import store
from django.contrib import messages
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
User = get_user_model()

# store setup
@login_required()
def store_setupAPI(request):
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

    return render(request, 'store_setup/store_setup.html', context)

#template loading
def load_templateAPI(request):
    org_id = request.GET.get('org_id')

    # Fetch the corresponding template based on org_id
    uitemp = UItemplate_setup.objects.filter(org_id=org_id).first()

    if uitemp:
        # Render the template to a string
        template_content = render_to_string(f'store_setup/{uitemp.uitemp_name}.html') if uitemp.uitemp_name else ""
    else:
        template_content = render_to_string('store_setup/not_found_temp.html')

    return JsonResponse({'template_content': template_content})


# store value click to show
@login_required()
def getStoreListAPI(request, store_id):

    try:
        store_list = get_object_or_404(store, store_id=store_id)

        store_Dtls = []

        store_Dtls.append({
            'store_id': store_list.store_id,
            'store_no': store_list.store_no,
            'store_name': store_list.store_name,
            'org_name': store_list.org_id.org_name if store_list.org_id else None,
            'branch_name': store_list.branch_id.branch_name if store_list.branch_id else None,
            'is_active': store_list.is_active,
            'is_general_store': store_list.is_general_store,
            'is_main_store': store_list.is_main_store,
            'is_sub_store': store_list.is_sub_store,
            'is_pos_report': store_list.is_pos_report,
        })

        context = {
            'store_Dtls': store_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# ======================================== Org wise store API ========================================
# Org store list show
@login_required()
def getOrgStoreDataAPI(request):
    orgstoreoption = request.GET.get('orgstoreoption')
    org_store_search_query = request.GET.get('org_store_search_query', '')
    org_id_wise_store_filter = request.GET.get('org_id_wise_store_filter')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if store_search_query is not empty
    if org_store_search_query:
        filter_kwargs |= Q(store_name__icontains=org_store_search_query) | Q(store_no__icontains=org_store_search_query)

    # Add org_id filter condition only if org_id_wise_store_filter is not empty
    if org_id_wise_store_filter.isdigit():
        filter_kwargs &= Q(org_id=org_id_wise_store_filter)

    # Add is_active filter condition based on orgstoreoption
    if orgstoreoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif orgstoreoption == 'false':
        filter_kwargs &= Q(is_active=False)

    org_store_data = store.objects.filter(is_org_store=True).filter(filter_kwargs)

    data = []
    for orgstore_item in org_store_data:
        org_name = orgstore_item.org_id.org_name if orgstore_item.org_id else None
        data.append({
            'store_id': orgstore_item.store_id,
            'store_no': orgstore_item.store_no,
            'store_name': orgstore_item.store_name,
            'org_name': org_name,
            'is_active': orgstore_item.is_active
        })

    return JsonResponse({'data': data})


# store add/update view org wise
@login_required()
def orgStoreAddUpdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    store_id = data.get('store_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('org')).first()
            branch_instance = branchslist.objects.filter(branch_id=data.get('branch_name')).first()

            # Check if supplier_id is provided for an update or add operation
            if store_id and store_id.isnumeric() and int(store_id) > 0:
                # This is an update operation
                store_data = store.objects.get(store_id=store_id)

                # Check if the provided store_no or store_name already exists for other store
                checkstore_no = store.objects.exclude(store_id=store_id).filter(Q(store_no=data.get('store_no')) & Q(org_id=org_instance)).exists()
                checkstore_name = store.objects.exclude(store_id=store_id).filter(Q(store_name=data.get('store_name')) & Q(org_id=org_instance)).exists()

                if checkstore_no:
                    return JsonResponse({'success': False, 'errmsg': 'Store No. Already Exists'})
                elif checkstore_name:
                    return JsonResponse({'success': False, 'errmsg': 'Store Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided store_no or store_name already exists for other items
                checkstore_no = store.objects.filter(Q(store_no=data.get('store_no')) & Q(org_id=org_instance)).exists()
                checkstore_name = store.objects.filter(Q(store_name=data.get('store_name')) & Q(org_id=org_instance)).exists()

                if checkstore_no:
                    return JsonResponse({'success': False, 'errmsg': 'Store No. Already Exists'})
                elif checkstore_name:
                    return JsonResponse({'success': False, 'errmsg': 'Store Name Already Exists'})
                
                # This is an add operation
                store_data = store()

            # Update or set the fields based on request data
            store_data.store_no = data.get('store_no')
            store_data.store_name = data.get('store_name')
            store_data.org_id = org_instance
            store_data.branch_id = branch_instance
            store_data.is_active = data.get('is_active', 0)
            store_data.is_org_store = data.get('is_org_store', 0)
            store_data.is_branch_store = data.get('is_branch_store', 0)
            store_data.is_general_store = data.get('is_general_store', 0)
            store_data.is_main_store = data.get('is_main_store', 0)
            store_data.is_sub_store = data.get('is_sub_store', 0)
            store_data.is_pos_report = data.get('is_pos_report', 0)
            store_data.ss_creator = request.user
            store_data.ss_modifier = request.user
            store_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)

# ======================================== Branch wise store API ========================================
# store list show
@login_required()
def get_store_dataAPI(request):
    storeoption = request.GET.get('storeoption')
    store_search_query = request.GET.get('store_search_query', '')
    org_id_wise_filter = request.GET.get('org_filter')
    branch_id_wise_filter = request.GET.get('branch_filter')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if store_search_query is not empty
    if store_search_query:
        filter_kwargs |= Q(store_name__icontains=store_search_query) | Q(store_no__icontains=store_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter.isdigit():
        filter_kwargs &= Q(org_id=org_id_wise_filter)
    
    if branch_id_wise_filter.isdigit():
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)

    # Add is_active filter condition based on storeoption
    if storeoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif storeoption == 'false':
        filter_kwargs &= Q(is_active=False)

    store_data = store.objects.filter(is_branch_store=True).filter(filter_kwargs)

    data = []
    for store_item in store_data:
        org_name = store_item.org_id.org_name if store_item.org_id else None
        branch_name = store_item.branch_id.branch_name if store_item.branch_id else None
        data.append({
            'store_id': store_item.store_id,
            'store_no': store_item.store_no,
            'store_name': store_item.store_name,
            'org_name': org_name,
            'branch_name': branch_name,
            'is_active': store_item.is_active
        })

    return JsonResponse({'data': data})


# store add/update view branch
@login_required()
def store_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    store_id = data.get('store_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('org')).first()
            branch_instance = branchslist.objects.filter(branch_id=data.get('branch_name')).first()

            # Check if supplier_id is provided for an update or add operation
            if store_id and store_id.isnumeric() and int(store_id) > 0:
                # This is an update operation
                store_data = store.objects.get(store_id=store_id)

                # Check if the provided store_no or store_name already exists for other store
                checkstore_no = store.objects.exclude(store_id=store_id).filter(Q(store_no=data.get('store_no')) & Q(branch_id=branch_instance)).exists()
                checkstore_name = store.objects.exclude(store_id=store_id).filter(Q(store_name=data.get('store_name')) & Q(branch_id=branch_instance)).exists()

                if checkstore_no:
                    return JsonResponse({'success': False, 'errmsg': 'Store No. Already Exists'})
                elif checkstore_name:
                    return JsonResponse({'success': False, 'errmsg': 'Store Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided store_no or store_name already exists for other items
                checkstore_no = store.objects.filter(Q(store_no=data.get('store_no')) & Q(branch_id=branch_instance)).exists()
                checkstore_name = store.objects.filter(Q(store_name=data.get('store_name')) & Q(branch_id=branch_instance)).exists()

                if checkstore_no:
                    return JsonResponse({'success': False, 'errmsg': 'Store No. Already Exists'})
                elif checkstore_name:
                    return JsonResponse({'success': False, 'errmsg': 'Store Name Already Exists'})
                
                # This is an add operation
                store_data = store()

            # Update or set the fields based on request data
            store_data.store_no = data.get('store_no')
            store_data.store_name = data.get('store_name')
            store_data.org_id = org_instance
            store_data.branch_id = branch_instance
            store_data.is_active = data.get('is_active', 0)
            store_data.is_org_store = data.get('is_org_store', 0)
            store_data.is_branch_store = data.get('is_branch_store', 0)
            store_data.is_general_store = data.get('is_general_store', 0)
            store_data.is_main_store = data.get('is_main_store', 0)
            store_data.is_sub_store = data.get('is_sub_store', 0)
            store_data.is_pos_report = data.get('is_pos_report', 0)
            store_data.ss_creator = request.user
            store_data.ss_modifier = request.user
            store_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)