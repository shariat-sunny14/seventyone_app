from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import SuppliersSetupForm, ManufacturerSetupForm, SuppliersUpdateForm, ManufacturerUpdateForm
from django.contrib import messages
from . models import suppliers, manufacturer
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


# Supplier & Manufecturer ViewAPI
@login_required()
def supplierManufecAPI(request):
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

    return render(request, 'supplier_manufacturer/supplier_manufacturer.html', context)

# supplier list show
@login_required()
def get_supplier_dataAPI(request):
    suppOption = request.GET.get('suppOption')
    suppFlagwise = request.GET.get('suppFlagwise')
    supp_search_query = request.GET.get('supp_search_query', '')
    org_id_wise_filter = request.GET.get('org_filter', '')


    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if supp_search_query is not empty
    if supp_search_query:
        filter_kwargs |= Q(supplier_name__icontains=supp_search_query) | Q(supplier_no__icontains=supp_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # supplier client wise filter
    if suppFlagwise == '2':
        filter_kwargs &= Q(supplier_flag=2)
    elif suppFlagwise == '3':
        filter_kwargs &= Q(manufacturer_flag=3)
    elif suppFlagwise == '4':
        filter_kwargs &= Q(b2bclient_flag=4)

    # Add is_active filter condition based on suppOption
    if suppOption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif suppOption == 'false':
        filter_kwargs &= Q(is_active=False)

    supp_data = suppliers.objects.filter(filter_kwargs)

    data = []
    for supp_item in supp_data:
        org_name = supp_item.org_id.org_name if supp_item.org_id else None
        data.append({
            'supplier_id': supp_item.supplier_id,
            'supplier_no': supp_item.supplier_no,
            'supplier_name': supp_item.supplier_name,
            'org_name': org_name,
            'supplier_flag': supp_item.supplier_flag,
            'manufacturer_flag': supp_item.manufacturer_flag,
            'b2bclient_flag': supp_item.b2bclient_flag,
            'is_active': supp_item.is_active
        })

    return JsonResponse({'data': data})


# supplier value click to show
@login_required()
def getSupplierListAPI(request, supplier_id):

    try:
        supplier_list = get_object_or_404(suppliers, supplier_id=supplier_id)

        supplier_Dtls = []

        supplier_Dtls.append({
            'supplier_id': supplier_list.supplier_id,
            'supplier_no': supplier_list.supplier_no,
            'supplier_name': supplier_list.supplier_name,
            'company_name': supplier_list.company_name,
            'org_name': supplier_list.org_id.org_name,
            'description': supplier_list.description,
            'address': supplier_list.address,
            'is_active': supplier_list.is_active,
            'supplier_flag': supplier_list.supplier_flag,
            'manufacturer_flag': supplier_list.manufacturer_flag,
            'b2bclient_flag': supplier_list.b2bclient_flag,
            'phone': supplier_list.phone,
            'mobile': supplier_list.mobile,
            'supplier_email': supplier_list.supplier_email,
            'supplier_fax': supplier_list.supplier_fax,
            'supplier_web': supplier_list.supplier_web,
            'account_no': supplier_list.account_no,
            'supplier_remarks': supplier_list.supplier_remarks,
            'contact_person': supplier_list.contact_person,
            'job_title': supplier_list.job_title,
            'con_per_Phone': supplier_list.con_per_Phone,
        })

        context = {
            'supplier_Dtls': supplier_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})


# supplier add/update view
@login_required()
def supplier_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    supplier_id = data.get('supplier_id')

    org_instance = organizationlst.objects.filter(org_id=data.get('org')).first()
    
    try:
        with transaction.atomic():
            # Check if supplier_id is provided for an update or add operation
            if supplier_id and supplier_id.isnumeric() and int(supplier_id) > 0:
                # This is an update operation
                supplier_data = suppliers.objects.get(supplier_id=supplier_id)

                # Check if the provided supplier_no or supplier_name already exists for other items
                checksupplier_no = suppliers.objects.exclude(supplier_id=supplier_id).filter(Q(supplier_no=data.get('supplier_no')) & Q(org_id=org_instance)).exists()
                checksupplier_name = suppliers.objects.exclude(supplier_id=supplier_id).filter(Q(supplier_name=data.get('supplier_name')) & Q(org_id=org_instance)).exists()

                if checksupplier_no:
                    return JsonResponse({'success': False, 'errmsg': 'Supplier No. Already Exists'})
                elif checksupplier_name:
                    return JsonResponse({'success': False, 'errmsg': 'Supplier Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided item_no or item_name already exists for other items
                checksupplier_no = suppliers.objects.filter(Q(supplier_no=data.get('supplier_no')) & Q(org_id=org_instance)).exists()
                checksupplier_name = suppliers.objects.filter(Q(supplier_name=data.get('supplier_name')) & Q(org_id=org_instance)).exists()

                if checksupplier_no:
                    return JsonResponse({'success': False, 'errmsg': 'Supplier No. Already Exists'})
                elif checksupplier_name:
                    return JsonResponse({'success': False, 'errmsg': 'Supplier Name Already Exists'})
                
                # This is an add operation
                supplier_data = suppliers()

            # Update or set the fields based on request data
            supplier_data.supplier_no = data.get('supplier_no')
            supplier_data.supplier_name = data.get('supplier_name')
            supplier_data.company_name = data.get('company_name')
            supplier_data.org_id = org_instance
            supplier_data.description = data.get('description')
            supplier_data.address = data.get('address')
            supplier_data.is_active = data.get('is_active', 0)
            supplier_data.supplier_flag = data.get('supplier_flag', 0)
            supplier_data.manufacturer_flag = data.get('manufacturer_flag', 0)
            supplier_data.b2bclient_flag = data.get('b2bclient_flag', 0)
            supplier_data.phone = data.get('phone')
            supplier_data.mobile = data.get('mobile')
            supplier_data.supplier_email = data.get('supplier_email')
            supplier_data.supplier_fax = data.get('supplier_fax')
            supplier_data.supplier_web = data.get('supplier_web')
            supplier_data.account_no = data.get('account_no')
            supplier_data.supplier_remarks = data.get('supplier_remarks')
            supplier_data.contact_person = data.get('contact_person')
            supplier_data.job_title = data.get('job_title')
            supplier_data.con_per_Phone = data.get('con_per_Phone')
            supplier_data.ss_creator = request.user
            supplier_data.ss_modifier = request.user
            supplier_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)

# manufecturer list show
@login_required()
def get_menufec_dataAPI(request):
    manuOption = request.GET.get('manuOption')
    menu_search_query = request.GET.get('menu_search_query', '')

    if manuOption in ['1', 'true', 'false']:
        # Handle '1', 'true', 'false' cases
        if manuOption == '1':
            menufec_data = manufacturer.objects.filter(Q(manufac_name__icontains=menu_search_query) | Q(manufac_no__icontains=menu_search_query)).order_by('manufac_name')
        elif manuOption == 'true':
            menufec_data = manufacturer.objects.filter(Q(is_active=True) & (Q(manufac_name__icontains=menu_search_query) | Q(manufac_no__icontains=menu_search_query))).order_by('manufac_name')
        elif manuOption == 'false':
            menufec_data = manufacturer.objects.filter(Q(is_active=False) & (Q(manufac_name__icontains=menu_search_query) | Q(manufac_no__icontains=menu_search_query))).order_by('manufac_name')

        data = [{'manufac_id': menuf.manufac_id, 'manufac_no': menuf.manufac_no, 'manufac_name': menuf.manufac_name, 'is_active': menuf.is_active} for menuf in menufec_data]

        return JsonResponse({'data': data})
    else:
        # If the option is not '1', 'true', or 'false', return an error message
        return JsonResponse({'error': 'Invalid option'})
    

# manufecturer value click to show
@login_required()
def getMenufecturerListAPI(request, manufac_id):

    try:
        menufecture_list = get_object_or_404(manufacturer, manufac_id=manufac_id)

        menufec_Dtls = []

        menufec_Dtls.append({
            'manufac_id': menufecture_list.manufac_id,
            'manufac_no': menufecture_list.manufac_no,
            'manufac_name': menufecture_list.manufac_name,
            'company_name': menufecture_list.company_name,
            'description': menufecture_list.description,
            'address': menufecture_list.address,
            'is_active': menufecture_list.is_active,
            'manufacturer_flag': menufecture_list.manufacturer_flag,
            'foreign_flag': menufecture_list.foreign_flag,
            'phone': menufecture_list.phone,
            'mobile': menufecture_list.mobile,
            'manufac_email': menufecture_list.manufac_email,
            'manufac_fax': menufecture_list.manufac_fax,
            'manufac_web': menufecture_list.manufac_web,
            'account_no': menufecture_list.account_no,
            'manufac_remarks': menufecture_list.manufac_remarks,
            'contact_person': menufecture_list.contact_person,
            'job_title': menufecture_list.job_title,
            'con_per_Phone': menufecture_list.con_per_Phone,
        })

        context = {
            'menufec_Dtls': menufec_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# supplier add/update view
@login_required()
def menufecture_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    manufac_id = data.get('manufac_id')

    try:
        with transaction.atomic():
            # Check if supplier_id is provided for an update or add operation
            if manufac_id and manufac_id.isnumeric() and int(manufac_id) > 0:
                # This is an update operation
                menufecture_data = manufacturer.objects.get(manufac_id=manufac_id)

                # Check if the provided supplier_no or supplier_name already exists for other items
                checkmanufac_no = manufacturer.objects.exclude(manufac_id=manufac_id).filter(manufac_no=data.get('manufac_no')).exists()
                checkmanufac_name = manufacturer.objects.exclude(manufac_id=manufac_id).filter(manufac_name=data.get('manufac_name')).exists()

                if checkmanufac_no:
                    return JsonResponse({'success': False, 'errmsg': 'Manufecture No. Already Exists'})
                elif checkmanufac_name:
                    return JsonResponse({'success': False, 'errmsg': 'Manufecture Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided item_no or item_name already exists for other items
                checkmanufac_no = manufacturer.objects.filter(manufac_no=data.get('manufac_no')).exists()
                checkmanufac_name = manufacturer.objects.filter(manufac_name=data.get('manufac_name')).exists()

                if checkmanufac_no:
                    return JsonResponse({'success': False, 'errmsg': 'Manufecture No. Already Exists'})
                elif checkmanufac_name:
                    return JsonResponse({'success': False, 'errmsg': 'Manufecture Name Already Exists'})
                
                # This is an add operation
                menufecture_data = manufacturer()

            # Update or set the fields based on request data
            menufecture_data.manufac_no = data.get('manufac_no')
            menufecture_data.manufac_name = data.get('manufac_name')
            menufecture_data.company_name = data.get('company_name')
            menufecture_data.description = data.get('description')
            menufecture_data.address = data.get('address')
            menufecture_data.is_active = data.get('is_active', 0)
            menufecture_data.manufacturer_flag = data.get('manufacturer_flag', 0)
            menufecture_data.foreign_flag = data.get('foreign_flag', 0)
            menufecture_data.phone = data.get('phone')
            menufecture_data.mobile = data.get('mobile')
            menufecture_data.manufac_email = data.get('manufac_email')
            menufecture_data.manufac_fax = data.get('manufac_fax')
            menufecture_data.manufac_web = data.get('manufac_web')
            menufecture_data.account_no = data.get('account_no')
            menufecture_data.manufac_remarks = data.get('manufac_remarks')
            menufecture_data.contact_person = data.get('contact_person')
            menufecture_data.job_title = data.get('job_title')
            menufecture_data.con_per_Phone = data.get('con_per_Phone')
            menufecture_data.ss_creator = request.user
            menufecture_data.ss_modifier = request.user
            menufecture_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)