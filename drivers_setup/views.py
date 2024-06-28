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
from . models import drivers_list
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def driversSetupManagerAPI(request):
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
    return render(request, 'drivers_setup/drivers_setup.html', op_stockData)


# add Drivers modal
@login_required()
def addDriversManageAPI(request):

    # Assuming 'country' is a variable representing a lookup code or value
    country_name = 'country'
    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'

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

    context = {
        'org_list': org_list,
        'countries': countries,
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
    }
    return render(request, 'drivers_setup/add_drivers.html', context)

# edit driver modal
@login_required()
def editDriverSetupManageAPI(request):

    # Assuming 'country' is a variable representing a lookup code or value
    country_name = 'country'
    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'

    countries = lookup_values.objects.filter(identify_code=country_name).all()
    divisions = lookup_values.objects.filter(identify_code=division_name).all()
    districts = lookup_values.objects.filter(identify_code=district_name).all()
    upazilas = lookup_values.objects.filter(identify_code=upazila_name).all()

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
        
        driver_data = {}
    if request.method == 'GET':
        data = request.GET
        driver_id = ''
        if 'driver_id' in data:
            driver_id = data['driver_id']
        if driver_id.isnumeric() and int(driver_id) > 0:
            driver_data = drivers_list.objects.filter(driver_id=driver_id).first()

    context = {
        'driver_data': driver_data,
        'org_list': org_list,
        'countries': countries,
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
    }
    return render(request, 'drivers_setup/edit_drivers.html', context)

# Drivers add/update view
@login_required()
def addUpdateDriversAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    driver_id = data.get('driver_id')
    org_id = data.get('org_id')
    branch_id = data.get('branch_id')

    country = data.get('country')
    division = data.get('division')
    district = data.get('district')
    upazila = data.get('upazila')


    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)

            country_instance = lookup_values.objects.get(lookup_id=country)
            division_instance = lookup_values.objects.get(lookup_id=division)
            district_instance = lookup_values.objects.get(lookup_id=district)
            upazila_instance = lookup_values.objects.get(lookup_id=upazila)

            # Check if driver_id is provided for an update or add operation
            if driver_id and driver_id.isnumeric() and int(driver_id) > 0:
                # This is an update operation
                driver_data = drivers_list.objects.get(driver_id=driver_id)

                # Check if the provided driver_no or driver_name already exists for other orgs
                check_driver_no = drivers_list.objects.exclude(driver_id=driver_id).filter(driver_no=data.get('driver_no')).exists()
                check_driver_name = drivers_list.objects.exclude(driver_id=driver_id).filter(driver_name=data.get('driver_name')).exists()

                if check_driver_no:
                    return JsonResponse({'success': False, 'errmsg': 'Driver No Already Exists'})
                elif check_driver_name:
                    return JsonResponse({'success': False, 'errmsg': 'Driver Name Already Exists'})
            else:
                # This is an add operation
                # Check if the provided driver_no or driver_name already exists for other items
                check_driver_no = drivers_list.objects.filter(driver_no=data.get('driver_no')).exists()
                check_driver_name = drivers_list.objects.filter(driver_name=data.get('driver_name')).exists()

                if check_driver_no:
                    return JsonResponse({'success': False, 'errmsg': 'Driver No Already Exists'})
                elif check_driver_name:
                    return JsonResponse({'success': False, 'errmsg': 'Driver Name Already Exists'})

                driver_data = drivers_list()

            # Update or set the fields based on request data
            driver_data.driver_no = data.get('driver_no')
            driver_data.driver_name = data.get('driver_name')
            driver_data.org_id = organization_instance
            driver_data.branch_id = branch_instance
            driver_data.is_active = data.get('is_active', 0)
            driver_data.country = country_instance
            driver_data.division = division_instance
            driver_data.district = district_instance
            driver_data.upazila = upazila_instance
            driver_data.email = data.get('email')
            driver_data.fax = data.get('fax')
            driver_data.website = data.get('website')
            driver_data.hotline = data.get('hotline')
            driver_data.phone = data.get('phone')
            driver_data.address = data.get('address')

            # Save the image file if provided
            if 'driver_picture' in request.FILES:
                img_file = request.FILES['driver_picture']
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

                # Save the resized logo to the organization's driver_picture field
                filename = default_storage.save('driver_pictures/' + img_file.name, ContentFile(output.read()))

                # Delete existing driver_picture before saving the new one
                if driver_data.driver_picture and driver_data.driver_picture.name != filename:
                    default_storage.delete(driver_data.driver_picture.path)

                driver_data.driver_picture = filename

            driver_data.ss_creator = request.user
            driver_data.ss_modifier = request.user
            driver_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


# get Drivers value and show in the dropdown
@login_required()
def getDriversOptionsAPI(request):
    if request.method == 'GET':
        id_org = request.GET.get('id_org')
        id_branch = request.GET.get('id_branch')

        if not id_org or not id_branch:
            return JsonResponse({'error': 'Missing organization or branch ID'}, status=400)

        try:
            org_instance = organizationlst.objects.get(pk=id_org)
            branch_instance = branchslist.objects.get(pk=id_branch)
        except (organizationlst.DoesNotExist, branchslist.DoesNotExist):
            return JsonResponse({'error': 'Invalid organization or branch ID'}, status=404)

        driver_options = drivers_list.objects.filter(is_active=True, org_id=org_instance, branch_id=branch_instance).values('driver_id', 'driver_name')
        
        return JsonResponse({'drivers_list': list(driver_options)})

    return JsonResponse({'error': 'Invalid request method'}, status=405)



@login_required()
def getDriversListsAPI(request):
    driverlst = drivers_list.objects.all()
    
    # Retrieve filter parameters from the frontend
    is_active = request.GET.get('is_active', None)
    org_id = request.GET.get('org_id', None)
    branch_id = request.GET.get('branch_id', None)

    # Create an empty filter dictionary to store dynamic filter conditions
    filter_conditions = {}

    # Apply filters based on conditions
    if is_active is not None:
        filter_conditions['is_active'] = is_active

    if org_id is not None:
        filter_conditions['org_id'] = org_id

    if branch_id is not None:
        filter_conditions['branch_id'] = branch_id

    # Apply dynamic filters to driverlst
    driver_data = driverlst.filter(**filter_conditions).all()
    
    # Convert driver data to a list of dictionaries
    driverData = []

    for driver in driver_data:
        picture_img_url = ''

        if driver.driver_picture:
            picture_img_url = driver.driver_picture.url

        driverData.append({
            'driver_id': driver.driver_id,
            'driver_name': driver.driver_name,
            'driver_picture': picture_img_url,
            'country': driver.country.name if driver.country else '',
            'division': driver.division.name if driver.division else '',
            'district': driver.district.name if driver.district else '',
            'upazila': driver.upazila.name if driver.upazila else '',
            'phone': driver.phone,
            'address': driver.address,
            'is_active': str(driver.is_active),  # Ensure boolean is converted to string for JavaScript
        })

    # Return the filtered data as JSON
    return JsonResponse({'driverlist_val': driverData})