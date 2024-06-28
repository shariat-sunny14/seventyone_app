from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ItemTypeSetupForm, ItemUoMSetupForm, ItemCategorySetupForm, ItemTypeUpdateForm, ItemUoMUpdateForm, ItemCategoryUpdateForm
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from . models import item_type, item_uom, item_category
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# main API
@login_required()
def TypeUomCategoryAPI(request):
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
    
    return render(request, 'type_category/main_type_category.html', context)

# ==================================================Type============================================
# Item type list show
@login_required()
def get_type_dataAPI(request):
    typeoption = request.GET.get('typeoption')
    type_search_query = request.GET.get('type_search_query', '')
    org_id_wise_filter = request.GET.get('org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if type_search_query is not empty
    if type_search_query:
        filter_kwargs |= Q(type_name__icontains=type_search_query) | Q(type_no__icontains=type_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Add is_active filter condition based on typeoption
    if typeoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif typeoption == 'false':
        filter_kwargs &= Q(is_active=False)

    type_data = item_type.objects.filter(filter_kwargs)

    data = []
    for type_item in type_data:
        org_name = type_item.org_id.org_name if type_item.org_id else None
        data.append({
            'type_id': type_item.type_id,
            'type_no': type_item.type_no,
            'type_name': type_item.type_name,
            'org_name': org_name,
            'is_active': type_item.is_active
        })

    return JsonResponse({'data': data})


# type value click to show
@login_required()
def getTypeListAPI(request, type_id):

    try:
        type_list = get_object_or_404(item_type, type_id=type_id)

        type_Dtls = []

        type_Dtls.append({
            'type_id': type_list.type_id,
            'type_no': type_list.type_no,
            'type_name': type_list.type_name,
            'org_name': type_list.org_id.org_name,
            'is_active': type_list.is_active,
        })

        context = {
            'type_Dtls': type_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# type add/update view
@login_required()
def type_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    type_id = data.get('type_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('org')).first()

            # Check if supplier_id is provided for an update or add operation
            if type_id and type_id.isnumeric() and int(type_id) > 0:
                # This is an update operation
                type_data = item_type.objects.get(type_id=type_id)

                # Check if the provided type_no or type_name already exists for other items
                checktype_no = item_type.objects.exclude(type_id=type_id).filter(Q(type_no=data.get('type_no')) & Q(org_id=org_instance)).exists()
                checktype_name = item_type.objects.exclude(type_id=type_id).filter(type_name=data.get('type_name'), org_id=org_instance).exists()

                if checktype_no:
                    return JsonResponse({'success': False, 'errmsg': 'Type No. Already Exists'})
                elif checktype_name:
                    return JsonResponse({'success': False, 'errmsg': 'Type Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided type_no or type_name already exists for other items
                checktype_no = item_type.objects.filter(type_no=data.get('type_no'), org_id=org_instance).exists()
                checktype_name = item_type.objects.filter(type_name=data.get('type_name'), org_id=org_instance).exists()

                if checktype_no:
                    return JsonResponse({'success': False, 'errmsg': 'Type No. Already Exists'})
                elif checktype_name:
                    return JsonResponse({'success': False, 'errmsg': 'Type Name Already Exists'})
                
                # This is an add operation
                type_data = item_type()

            # Update or set the fields based on request data
            type_data.type_no = data.get('type_no')
            type_data.type_name = data.get('type_name')
            type_data.org_id = org_instance
            type_data.is_active = data.get('is_active', 0)
            type_data.ss_creator = request.user
            type_data.ss_modifier = request.user
            type_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)

# ==================================================UOM============================================
# Item UoM list show
@login_required()
def get_uom_dataAPI(request):
    uomoption = request.GET.get('uomoption')
    uom_search_query = request.GET.get('uom_search_query', '')
    uomorg_id_wise_filter = request.GET.get('uom_org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if uom_search_query is not empty
    if uom_search_query:
        filter_kwargs |= Q(item_uom_name__icontains=uom_search_query) | Q(item_uom_no__icontains=uom_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if uomorg_id_wise_filter:
        filter_kwargs &= Q(org_id=uomorg_id_wise_filter)

    # Add is_active filter condition based on typeoption
    if uomoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif uomoption == 'false':
        filter_kwargs &= Q(is_active=False)

    uom_data = item_uom.objects.filter(filter_kwargs)

    data = []
    for uom_item in uom_data:
        org_name = uom_item.org_id.org_name if uom_item.org_id else None
        data.append({
            'item_uom_id': uom_item.item_uom_id,
            'item_uom_no': uom_item.item_uom_no,
            'item_uom_name': uom_item.item_uom_name,
            'org_name': org_name,
            'is_active': uom_item.is_active
        })

    return JsonResponse({'data': data})

# uom value click to show
@login_required()
def getUoMListAPI(request, item_uom_id):

    try:
        uom_list = get_object_or_404(item_uom, item_uom_id=item_uom_id)

        uom_Dtls = []

        uom_Dtls.append({
            'item_uom_id': uom_list.item_uom_id,
            'item_uom_no': uom_list.item_uom_no,
            'item_uom_name': uom_list.item_uom_name,
            'org_name': uom_list.org_id.org_name,
            'is_active': uom_list.is_active,
        })

        context = {
            'uom_Dtls': uom_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})


# uom add/update view
@login_required()
def uom_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    item_uom_id = data.get('item_uom_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('uom_org')).first()

            # Check if supplier_id is provided for an update or add operation
            if item_uom_id and item_uom_id.isnumeric() and int(item_uom_id) > 0:
                # This is an update operation
                uom_data = item_uom.objects.get(item_uom_id=item_uom_id)

                # Check if the provided item_uom_no or item_uom_name already exists for other items
                checkuom_no = item_uom.objects.exclude(item_uom_id=item_uom_id).filter(Q(item_uom_no=data.get('item_uom_no')) & Q(org_id=org_instance)).exists()
                checkuom_name = item_uom.objects.exclude(item_uom_id=item_uom_id).filter(Q(item_uom_name=data.get('item_uom_name')) & Q(org_id=org_instance)).exists()

                if checkuom_no:
                    return JsonResponse({'success': False, 'errmsg': 'Type No. Already Exists'})
                elif checkuom_name:
                    return JsonResponse({'success': False, 'errmsg': 'Type Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided item_uom_no or item_uom_name already exists for other items
                checkuom_no = item_uom.objects.filter(Q(item_uom_no=data.get('item_uom_no')) & Q(org_id=org_instance)).exists()
                checkuom_name = item_uom.objects.filter(Q(item_uom_name=data.get('item_uom_name')) & Q(org_id=org_instance)).exists()

                if checkuom_no:
                    return JsonResponse({'success': False, 'errmsg': 'Type No. Already Exists'})
                elif checkuom_name:
                    return JsonResponse({'success': False, 'errmsg': 'Type Name Already Exists'})
                
                # This is an add operation
                uom_data = item_uom()

            # Update or set the fields based on request data
            uom_data.item_uom_no = data.get('item_uom_no')
            uom_data.item_uom_name = data.get('item_uom_name')
            uom_data.org_id = org_instance
            uom_data.is_active = data.get('is_active', 0)
            uom_data.ss_creator = request.user
            uom_data.ss_modifier = request.user
            uom_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


# ==================================================Category============================================
# Item Category list show
@login_required()
def get_category_dataAPI(request):
    catoption = request.GET.get('catoption')
    cat_search_query = request.GET.get('cat_search_query', '')
    catorg_id_wise_filter = request.GET.get('cat_org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if cat_search_query is not empty
    if cat_search_query:
        filter_kwargs |= Q(category_name__icontains=cat_search_query) | Q(category_no__icontains=cat_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if catorg_id_wise_filter:
        filter_kwargs &= Q(org_id=catorg_id_wise_filter)

    # Add is_active filter condition based on typeoption
    if catoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif catoption == 'false':
        filter_kwargs &= Q(is_active=False)

    cat_data = item_category.objects.filter(filter_kwargs)

    data = []
    for cat_item in cat_data:
        org_name = cat_item.org_id.org_name if cat_item.org_id else None
        data.append({
            'category_id': cat_item.category_id,
            'category_no': cat_item.category_no,
            'category_name': cat_item.category_name,
            'org_name': org_name,
            'is_active': cat_item.is_active
        })

    return JsonResponse({'data': data})

    if catoption in ['1', 'true', 'false']:
        # Handle '1', 'true', 'false' cases
        if catoption == '1':
            cat_data = item_category.objects.filter(Q(category_name__icontains=cat_search_query) | Q(category_no__icontains=cat_search_query)).order_by('category_name')
        elif catoption == 'true':
            cat_data = item_category.objects.filter(Q(is_active=True) & (Q(category_name__icontains=cat_search_query) | Q(category_no__icontains=cat_search_query))).order_by('category_name')
        elif catoption == 'false':
            cat_data = item_category.objects.filter(Q(is_active=False) & (Q(category_name__icontains=cat_search_query) | Q(category_no__icontains=cat_search_query))).order_by('category_name')

        data = [{'category_id': catD.category_id, 'category_no': catD.category_no, 'category_name': catD.category_name, 'is_active': catD.is_active} for catD in cat_data]

        return JsonResponse({'data': data})
    else:
        # If the option is not '1', 'true', or 'false', return an error message
        return JsonResponse({'error': 'Invalid option'})
    

# Category value click to show
@login_required()
def getCategoryListAPI(request, category_id):

    try:
        cat_list = get_object_or_404(item_category, category_id=category_id)

        cat_Dtls = []

        cat_Dtls.append({
            'category_id': cat_list.category_id,
            'category_no': cat_list.category_no,
            'category_name': cat_list.category_name,
            'org_name': cat_list.org_id.org_name,
            'is_active': cat_list.is_active,
        })

        context = {
            'cat_Dtls': cat_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# category add/update view
@login_required()
def category_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    category_id = data.get('category_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('cat_org')).first()

            # Check if category_id is provided for an update or add operation
            if category_id and category_id.isnumeric() and int(category_id) > 0:
                # This is an update operation
                cat_data = item_category.objects.get(category_id=category_id)

                # Check if the provided category_no or category_name already exists for other items
                checkcategory_no = item_category.objects.exclude(category_id=category_id).filter(Q(category_no=data.get('category_no')) & Q(org_id=org_instance)).exists()
                checkcategory_name = item_category.objects.exclude(category_id=category_id).filter(Q(category_name=data.get('category_name')) & Q(org_id=org_instance)).exists()

                if checkcategory_no:
                    return JsonResponse({'success': False, 'errmsg': 'Category No. Already Exists'})
                elif checkcategory_name:
                    return JsonResponse({'success': False, 'errmsg': 'Category Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided category_no or category_name already exists for other items
                checkcategory_no = item_category.objects.filter(Q(category_no=data.get('category_no')) & Q(org_id=org_instance)).exists()
                checkcategory_name = item_category.objects.filter(Q(category_name=data.get('category_name')) & Q(org_id=org_instance)).exists()

                if checkcategory_no:
                    return JsonResponse({'success': False, 'errmsg': 'Category No. Already Exists'})
                elif checkcategory_name:
                    return JsonResponse({'success': False, 'errmsg': 'Category Name Already Exists'})
                
                # This is an add operation
                cat_data = item_category()

            # Update or set the fields based on request data
            cat_data.category_no = data.get('category_no')
            cat_data.category_name = data.get('category_name')
            cat_data.org_id = org_instance
            cat_data.is_active = data.get('is_active', 0)
            cat_data.ss_creator = request.user
            cat_data.ss_modifier = request.user
            cat_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)