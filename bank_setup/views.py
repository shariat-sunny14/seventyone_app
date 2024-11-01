import sys
import json
from PIL import Image
from io import BytesIO
from django.db.models import Q
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core import serializers
from datetime import datetime
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import transaction
from user_setup.models import lookup_values
from organizations.models import branchslist, organizationlst
from user_setup.models import lookup_values
from . models import bank_lists
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def bankSetupManagerAPI(request):
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

    op_stockData = {
        'org_list': org_list,
    }
    return render(request, 'bank_setup/banks_setup.html', op_stockData)


# add banks modal
@login_required()
def addBankSetupManageAPI(request):

    # Assuming 'country' is a variable representing a lookup code or value
    country_name = 'country'
    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'
    bank_branch_name = 'bank_branch'

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

    countries = lookup_values.objects.filter(identify_code=country_name).all()
    divisions = lookup_values.objects.filter(identify_code=division_name).all()
    districts = lookup_values.objects.filter(identify_code=district_name).all()
    upazilas = lookup_values.objects.filter(identify_code=upazila_name).all()
    bankBranch = lookup_values.objects.filter(identify_code=bank_branch_name).all()

    context = {
        'org_list': org_list,
        'countries': countries,
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
        'bankBranch': bankBranch,
    }
    return render(request, 'bank_setup/add_banks.html', context)

# edit bank modal
@login_required()
def editBankSetupManageAPI(request):

    # Assuming 'country' is a variable representing a lookup code or value
    country_name = 'country'
    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'
    bank_branch_name = 'bank_branch'

    countries = lookup_values.objects.filter(identify_code=country_name).all()
    divisions = lookup_values.objects.filter(identify_code=division_name).all()
    districts = lookup_values.objects.filter(identify_code=district_name).all()
    upazilas = lookup_values.objects.filter(identify_code=upazila_name).all()
    bankBranch = lookup_values.objects.filter(identify_code=bank_branch_name).all()

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
        
        bank_data = {}
    if request.method == 'GET':
        data = request.GET
        bank_id = ''
        if 'bank_id' in data:
            bank_id = data['bank_id']
        if bank_id.isnumeric() and int(bank_id) > 0:
            bank_data = bank_lists.objects.filter(bank_id=bank_id).first()

    context = {
        'bank_data': bank_data,
        'org_list': org_list,
        'countries': countries,
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
        'bankBranch': bankBranch,
    }
    return render(request, 'bank_setup/edit_banks.html', context)

# banks add/update view
@login_required()
def addUpdateBankSetupAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    bank_id = data.get('bank_id')
    org_id = data.get('org_id')

    country = data.get('country')
    division = data.get('division')
    district = data.get('district')
    upazila = data.get('upazila')
    bank_branch_name = data.get('bank_branch_name')
    email = data.get('email')


    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)

            country_instance = lookup_values.objects.get(lookup_id=country) if country else None
            division_instance = lookup_values.objects.get(lookup_id=division) if division else None
            district_instance = lookup_values.objects.get(lookup_id=district) if district else None
            upazila_instance = lookup_values.objects.get(lookup_id=upazila) if upazila else None
            bank_branch_instance = lookup_values.objects.get(lookup_id=bank_branch_name) if bank_branch_name else None

            # Check if bank_id is provided for an update or add operation
            if bank_id and bank_id.isnumeric() and int(bank_id) > 0:
                # This is an update operation
                bank_data = bank_lists.objects.get(bank_id=bank_id)

                # Check if the provided bank_no or bank_name already exists for other orgs
                check_bank_no = bank_lists.objects.exclude(bank_id=bank_id).filter(bank_no=data.get('bank_no')).exists()
                check_bank_name = bank_lists.objects.exclude(bank_id=bank_id).filter(bank_name=data.get('bank_name')).exists()

                if check_bank_no:
                    return JsonResponse({'success': False, 'errmsg': 'Bank No Already Exists'})
                elif check_bank_name:
                    return JsonResponse({'success': False, 'errmsg': 'Bank Name Already Exists'})
            else:
                # This is an add operation
                # Check if the provided bank_no or bank_name already exists for other items
                check_bank_no = bank_lists.objects.filter(bank_no=data.get('bank_no')).exists()
                check_bank_name = bank_lists.objects.filter(bank_name=data.get('bank_name')).exists()

                if check_bank_no:
                    return JsonResponse({'success': False, 'errmsg': 'Bank No Already Exists'})
                elif check_bank_name:
                    return JsonResponse({'success': False, 'errmsg': 'Bank Name Already Exists'})

                bank_data = bank_lists()

            # Update or set the fields based on request data
            bank_data.bank_no = data.get('bank_no')
            bank_data.bank_name = data.get('bank_name')
            bank_data.account_no = data.get('account_no')
            bank_data.org_id = organization_instance
            bank_data.is_active = data.get('is_active', 0)
            bank_data.country = country_instance
            bank_data.division = division_instance
            bank_data.district = district_instance
            bank_data.upazila = upazila_instance
            bank_data.bank_branch = bank_branch_instance
            bank_data.email = email
            bank_data.fax = data.get('fax')
            bank_data.website = data.get('website')
            bank_data.hotline = data.get('hotline')
            bank_data.phone = data.get('phone')
            bank_data.address = data.get('address')

            # Save the image file if provided
            if 'bank_picture' in request.FILES:
                img_file = request.FILES['bank_picture']
                picture_image = Image.open(img_file)

                # Check if the image has an alpha channel (transparency)
                if picture_image.mode in ('RGBA', 'LA') or (picture_image.mode == 'P' and 'transparency' in picture_image.info):
                    # Convert image to RGB if it has an alpha channel
                    picture_image = picture_image.convert('RGB')

                # Resize the image to fit within 300x300 while maintaining aspect ratio
                picture_image.thumbnail((300, 300))

                # Convert the image to BytesIO and save to Django's ContentFile
                output = BytesIO()
                picture_image.save(output, format='JPEG')
                output.seek(0)

                # Save the resized logo to the organization's bank_picture field
                filename = default_storage.save('bank_pictures/' + img_file.name, ContentFile(output.read()))

                # Delete existing bank_picture before saving the new one
                if bank_data.bank_picture and bank_data.bank_picture.name != filename:
                    default_storage.delete(bank_data.bank_picture.path)

                bank_data.bank_picture = filename

            bank_data.ss_creator = request.user
            bank_data.ss_modifier = request.user
            bank_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


# get banks value and show in the dropdown
@login_required()
def getBankSetupOptionsAPI(request):
    if request.method == 'GET':
        id_org = request.GET.get('id_org')

        if not id_org:
            return JsonResponse({'error': 'Missing organization or branch ID'}, status=400)

        try:
            org_instance = organizationlst.objects.get(pk=id_org)
        except (organizationlst.DoesNotExist, branchslist.DoesNotExist):
            return JsonResponse({'error': 'Invalid organization or branch ID'}, status=404)

        bank_options = bank_lists.objects.filter(is_active=True, org_id=org_instance).values('bank_id', 'bank_name')
        
        return JsonResponse({'bank_lists': list(bank_options)})

    return JsonResponse({'error': 'Invalid request method'}, status=405)



@login_required()
def getBankSetupListsAPI(request):
    banklst = bank_lists.objects.all()
    
    # Retrieve filter parameters from the frontend
    is_active = request.GET.get('is_active', None)
    org_id = request.GET.get('org_id', None)

    # Create an empty filter dictionary to store dynamic filter conditions
    filter_conditions = {}

    # Apply filters based on conditions
    if is_active is not None:
        filter_conditions['is_active'] = is_active

    if org_id is not None:
        filter_conditions['org_id'] = org_id

    # Apply dynamic filters to banklst
    bank_data = banklst.filter(**filter_conditions).all()
    
    # Convert bank data to a list of dictionaries
    bankData = []

    for bank in bank_data:
        picture_img_url = ''

        if bank.bank_picture:
            picture_img_url = bank.bank_picture.url

        bankData.append({
            'bank_id': bank.bank_id,
            'bank_name': bank.bank_name,
            'account_no': bank.account_no,
            'bank_branch': bank.bank_branch.name if bank.bank_branch else '',
            'bank_picture': picture_img_url,
            'phone': bank.phone,
            'address': bank.address,
            'is_active': str(bank.is_active),  # Ensure boolean is converted to string for JavaScript
        })

    # Return the filtered data as JSON
    return JsonResponse({'banklist_val': bankData})