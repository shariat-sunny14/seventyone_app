import sys
import json
from PIL import Image
from io import BytesIO
from django.db.models import Q
from django.db import transaction
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from user_setup.models import lookup_values
from . models import organizationlst, branchslist
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def organizationSetupAPI(request):

    # Assuming 'country' is a variable representing a lookup code or value
    country_name = 'country'
    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'

    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        organizations = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        organizations = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        organizations = []

    
    countries = lookup_values.objects.filter(identify_code=country_name).all()
    divisions = lookup_values.objects.filter(identify_code=division_name).all()
    districts = lookup_values.objects.filter(identify_code=district_name).all()
    upazilas = lookup_values.objects.filter(identify_code=upazila_name).all()

    # organization = organizationlst.objects.filter(is_active=True).all()

    context = {
        'countries': countries,
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
        'organization': organizations,
    }
    
    return render(request, 'organization/organization_manager.html', context)


# organization list show
@login_required()
def get_organization_dataAPI(request):
    user = request.user
    orgoption = request.GET.get('orgoption')
    org_search_query = request.GET.get('org_search_query', '')

    # Check if the user is a superuser
    if user.is_superuser:
        # If superuser, return all organizationlst objects
        if orgoption in ['1', 'true', 'false']:
            # Handle '1', 'true', 'false' cases
            if orgoption == '1':
                org_data = organizationlst.objects.filter(Q(org_name__icontains=org_search_query) | Q(org_no__icontains=org_search_query)).order_by('org_name')
            elif orgoption == 'true':
                org_data = organizationlst.objects.filter(Q(is_active=True) & (Q(org_name__icontains=org_search_query) | Q(org_no__icontains=org_search_query))).order_by('org_name')
            elif orgoption == 'false':
                org_data = organizationlst.objects.filter(Q(is_active=False) & (Q(org_name__icontains=org_search_query) | Q(org_no__icontains=org_search_query))).order_by('org_name')

            data = [{'org_id': org.org_id, 'org_no': org.org_no, 'org_name': org.org_name, 'is_active': org.is_active} for org in org_data]
            return JsonResponse({'data': data})
        else:
            # If the option is not '1', 'true', or 'false', return an error message
            return JsonResponse({'error': 'Invalid option'})
    
    else:
        # Check if the user has an associated organization (org_id is not null in User model)
        if user.org_id is not None:
            org_id = user.org_id

            if orgoption in ['1', 'true', 'false']:
                # Handle '1', 'true', 'false' cases
                if orgoption == '1':
                    # Include org_id for non-superusers when orgoption is '1'
                    org_data = organizationlst.objects.filter(Q(org_id=org_id) & (Q(org_name__icontains=org_search_query) | Q(org_no__icontains=org_search_query))).order_by('org_name')
                elif orgoption == 'true':
                    org_data = organizationlst.objects.filter(Q(is_active=True, org_id=org_id) & (Q(org_name__icontains=org_search_query) | Q(org_no__icontains=org_search_query))).order_by('org_name')
                elif orgoption == 'false':
                    org_data = organizationlst.objects.filter(Q(is_active=False, org_id=org_id) & (Q(org_name__icontains=org_search_query) | Q(org_no__icontains=org_search_query))).order_by('org_name')

                data = [{'org_id': org.org_id, 'org_no': org.org_no, 'org_name': org.org_name, 'is_active': org.is_active} for org in org_data]
                return JsonResponse({'data': data})
            else:
                # If the option is not '1', 'true', or 'false', return an error message
                return JsonResponse({'error': 'Invalid option'})
            
        return JsonResponse({'error': 'User does not have an associated organization'})
    

# organization value click to show
@login_required()
def getOrganizationListAPI(request, org_id):

    try:
        org_list = get_object_or_404(organizationlst, org_id=org_id)

        org_Dtls = []

        org_Dtls.append({
            'org_id': org_list.org_id,
            'org_no': org_list.org_no,
            'org_name': org_list.org_name,
            'is_active': org_list.is_active,
            'country': org_list.country,
            'division': org_list.division,
            'district': org_list.district,
            'upazila': org_list.upazila,
            'email': org_list.email,
            'fax': org_list.fax,
            'website': org_list.website,
            'hotline': org_list.hotline,
            'phone': org_list.phone,
            'org_logo': org_list.org_logo.url if org_list.org_logo else None,
            'address': org_list.address,
            'description': org_list.description,
        })

        context = {
            'org_Dtls': org_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# organization add/update view
@login_required()
def organization_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org_id')

    try:
        with transaction.atomic():
            # Check if org_id is provided for an update or add operation
            if org_id and org_id.isnumeric() and int(org_id) > 0:
                # This is an update operation
                org_data = organizationlst.objects.get(org_id=org_id)

                # Check if the provided org_no or org_name already exists for other orgs
                check_org_no = organizationlst.objects.exclude(org_id=org_id).filter(org_no=data.get('org_no')).exists()
                check_org_name = organizationlst.objects.exclude(org_id=org_id).filter(org_name=data.get('org_name')).exists()

                if check_org_no:
                    return JsonResponse({'success': False, 'errmsg': 'Org No. Already Exists'})
                elif check_org_name:
                    return JsonResponse({'success': False, 'errmsg': 'Org Name Already Exists'})
            else:
                # This is an add operation
                # Check if the provided org_no or org_name already exists for other items
                check_org_no = organizationlst.objects.filter(org_no=data.get('org_no')).exists()
                check_org_name = organizationlst.objects.filter(org_name=data.get('org_name')).exists()

                if check_org_no:
                    return JsonResponse({'success': False, 'errmsg': 'Org No. Already Exists'})
                elif check_org_name:
                    return JsonResponse({'success': False, 'errmsg': 'Org Name Already Exists'})

                org_data = organizationlst()

            # Update or set the fields based on request data
            org_data.org_no = data.get('org_no')
            org_data.org_name = data.get('org_name')
            org_data.is_active = data.get('is_active', 0)
            org_data.country = data.get('country')
            org_data.division = data.get('division')
            org_data.district = data.get('district')
            org_data.upazila = data.get('upazila')
            org_data.email = data.get('email')
            org_data.fax = data.get('fax')
            org_data.website = data.get('website')
            org_data.hotline = data.get('hotline')
            org_data.phone = data.get('phone')
            org_data.address = data.get('address')
            org_data.description = data.get('description')

            # Save the image file if provided
            if 'org_logo' in request.FILES:
                logo_file = request.FILES['org_logo']
                logo_image = Image.open(logo_file)

                # Check if the image has an alpha channel (transparency)
                if logo_image.mode in ('RGBA', 'LA') or (logo_image.mode == 'P' and 'transparency' in logo_image.info):
                    # Convert image to RGB if it has an alpha channel
                    logo_image = logo_image.convert('RGB')

                # Resize the image to fit within 300x300 while maintaining aspect ratio
                logo_image.thumbnail((300, 300))

                # Convert the image to BytesIO and save to Django's ContentFile
                output = BytesIO()
                logo_image.save(output, format='JPEG')
                output.seek(0)

                # Save the resized logo to the organization's org_logo field
                filename = default_storage.save('org_logos/' + logo_file.name, ContentFile(output.read()))

                # Delete existing org_logo before saving the new one
                if org_data.org_logo and org_data.org_logo.name != filename:
                    default_storage.delete(org_data.org_logo.path)

                org_data.org_logo = filename

            org_data.ss_creator = request.user
            org_data.ss_modifier = request.user
            org_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)



# ==========================================================XXXX Branchs XXXX==========================================================
# organization list show
@login_required()
def getBranchsDataAPI(request):
    user = request.user
    branchoption = request.GET.get('branchoption')
    branch_search_query = request.GET.get('branch_search_query', '')

    # Check if the user is a superuser
    if user.is_superuser:
        # If superuser, return all branchslist objects
        if branchoption in ['1', 'true', 'false']:
            # Handle '1', 'true', 'false' cases
            if branchoption == '1':
                branch_data = branchslist.objects.filter(
                    Q(branch_name__icontains=branch_search_query) | Q(branch_no__icontains=branch_search_query)
                ).order_by('branch_name')
            elif branchoption == 'true':
                branch_data = branchslist.objects.filter(
                    Q(is_active=True) & (Q(branch_name__icontains=branch_search_query) | Q(branch_no__icontains=branch_search_query))
                ).order_by('branch_name')
            elif branchoption == 'false':
                branch_data = branchslist.objects.filter(
                    Q(is_active=False) & (Q(branch_name__icontains=branch_search_query) | Q(branch_no__icontains=branch_search_query))
                ).order_by('branch_name')

            branch_values_dict = {}

            for branch in branch_data:
                org_id = branch.org_id.org_id
                branch_values = {
                    'branch_id': branch.branch_id,
                    'branch_no': branch.branch_no,
                    'branch_name': branch.branch_name,
                    'is_active': branch.is_active,
                    # Add other fields as needed
                }

                if org_id in branch_values_dict:
                    branch_values_dict[org_id]['details'].append(branch_values)
                else:
                    branch_values_dict[org_id] = {
                        'org_id': branch.org_id.org_id,
                        'org_no': branch.org_id.org_no,
                        'org_name': branch.org_id.org_name,
                        'is_active': branch.org_id.is_active,
                        'details': [branch_values],
                    }

            return JsonResponse({'data': list(branch_values_dict.values())})
            
        else:
            # If the option is not '1', 'true', or 'false', return an error message
            return JsonResponse({'error': 'Invalid option'})
    
    else:
        # Check if the user has an associated organization (org_id is not null in User model)
        if user.branch_id is not None:
            branch_id = user.branch_id

            if branchoption in ['1', 'true', 'false']:
                # Handle '1', 'true', 'false' cases
                if branchoption == '1':
                    # Include org_id for non-superusers when orgoption is '1'
                    branch_data = branchslist.objects.filter(
                        Q(branch_id=branch_id) & (Q(branch_name__icontains=branch_search_query) | Q(branch_no__icontains=branch_search_query))
                    ).order_by('branch_name')
                elif branchoption == 'true':
                    branch_data = branchslist.objects.filter(
                        Q(is_active=True, branch_id=branch_id) & (Q(branch_name__icontains=branch_search_query) | Q(branch_no__icontains=branch_search_query))
                    ).order_by('branch_name')
                elif branchoption == 'false':
                    branch_data = branchslist.objects.filter(
                        Q(is_active=False, branch_id=branch_id) & (Q(branch_name__icontains=branch_search_query) | Q(branch_no__icontains=branch_search_query))
                    ).order_by('branch_name')
                
                branch_values_dict = {}

                for branch in branch_data:
                    org_id = branch.org_id.org_id
                    branch_values = {
                        'branch_id': branch.branch_id,
                        'branch_no': branch.branch_no,
                        'branch_name': branch.branch_name,
                        'is_active': branch.is_active,
                        # Add other fields as needed
                    }

                    if org_id in branch_values_dict:
                        branch_values_dict[org_id]['details'].append(branch_values)
                    else:
                        branch_values_dict[org_id] = {
                            'org_id': branch.org_id.org_id,
                            'org_no': branch.org_id.org_no,
                            'org_name': branch.org_id.org_name,
                            'is_active': branch.org_id.is_active,
                            'details': [branch_values],
                        }

                return JsonResponse({'data': list(branch_values_dict.values())})

            else:
                # If the option is not '1', 'true', or 'false', return an error message
                return JsonResponse({'error': 'Invalid option'})
    

# select branch id wise value
@login_required()
def selectBranchListAPI(request, branch_id):

    try:
        branch_list = get_object_or_404(branchslist, branch_id=branch_id)

        branch_Dtls = []

        branch_Dtls.append({
            'branch_id': branch_list.branch_id,
            'branch_no': branch_list.branch_no,
            'branch_name': branch_list.branch_name,
            'bran_org_id': branch_list.org_id.org_id,
            'is_main_branch': branch_list.is_main_branch,
            'is_sub_branch': branch_list.is_sub_branch,
            'is_active': branch_list.is_active,
            'country': branch_list.country,
            'division': branch_list.division,
            'district': branch_list.district,
            'upazila': branch_list.upazila,
            'email': branch_list.email,
            'fax': branch_list.fax,
            'website': branch_list.website,
            'hotline': branch_list.hotline,
            'phone': branch_list.phone,
            'branch_logo': branch_list.branch_logo.url if branch_list.branch_logo else None,
            'address': branch_list.address,
            'description': branch_list.description,
        })

        context = {
            'branch_Dtls': branch_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    


# branch add/update view
@login_required()
def branchAddUpdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    branch_id = data.get('branch_id')

    try:
        with transaction.atomic():
            # Check if branch_id is provided for an update or add operation
            if branch_id and branch_id.isnumeric() and int(branch_id) > 0:
                # This is an update operation
                branch_data = branchslist.objects.get(branch_id=branch_id)

                # Check if the provided branch_no or branch_name already exists for other orgs
                check_branch_no = branchslist.objects.exclude(branch_id=branch_id).filter(branch_no=data.get('branch_no')).exists()
                check_branch_name = branchslist.objects.exclude(branch_id=branch_id).filter(branch_name=data.get('branch_name')).exists()

                if check_branch_no:
                    return JsonResponse({'success': False, 'errmsg': 'Branch No. Already Exists'})
                elif check_branch_name:
                    return JsonResponse({'success': False, 'errmsg': 'Branch Name Already Exists'})
            else:
                # This is an add operation
                # Check if the provided branch_no or branch_name already exists for other items
                check_branch_no = branchslist.objects.filter(branch_no=data.get('branch_no')).exists()
                check_branch_name = branchslist.objects.filter(branch_name=data.get('branch_name')).exists()

                if check_branch_no:
                    return JsonResponse({'success': False, 'errmsg': 'Branch No. Already Exists'})
                elif check_branch_name:
                    return JsonResponse({'success': False, 'errmsg': 'Branch Name Already Exists'})

                branch_data = branchslist()

            org_instance, created = organizationlst.objects.get_or_create(org_id=data.get('branch_org_name'))

            # Update or set the fields based on request data
            branch_data.branch_no = data.get('branch_no')
            branch_data.branch_name = data.get('branch_name')
            branch_data.org_id = org_instance
            branch_data.is_main_branch = data.get('main_branch', 0)
            branch_data.is_sub_branch = data.get('sub_branch', 0)
            branch_data.is_active = data.get('is_active', 0)
            branch_data.country = data.get('branch_country')
            branch_data.division = data.get('branch_division')
            branch_data.district = data.get('branch_district')
            branch_data.upazila = data.get('branch_upazila')
            branch_data.email = data.get('branch_email')
            branch_data.fax = data.get('branch_fax')
            branch_data.website = data.get('branch_website')
            branch_data.hotline = data.get('branch_hotline')
            branch_data.phone = data.get('branch_phone')
            branch_data.address = data.get('branch_address')
            branch_data.description = data.get('branch_description')

            # Save the image file if provided
            if 'branch_logo' in request.FILES:
                logo_file = request.FILES['branch_logo']
                logo_image = Image.open(logo_file)

                # Check if the image has an alpha channel (transparency)
                if logo_image.mode in ('RGBA', 'LA') or (logo_image.mode == 'P' and 'transparency' in logo_image.info):
                    # Convert image to RGB if it has an alpha channel
                    logo_image = logo_image.convert('RGB')

                # Resize the image to fit within 300x300 while maintaining aspect ratio
                logo_image.thumbnail((300, 300))

                # Convert the image to BytesIO and save to Django's ContentFile
                output = BytesIO()
                logo_image.save(output, format='JPEG')
                output.seek(0)

                # Save the resized logo to the organization's org_logo field
                filename = default_storage.save('branch_logo/' + logo_file.name, ContentFile(output.read()))

                # Delete existing branch_logo before saving the new one
                if branch_data.branch_logo and branch_data.branch_logo.name != filename:
                    default_storage.delete(branch_data.branch_logo.path)

                branch_data.branch_logo = filename

            branch_data.ss_creator = request.user
            branch_data.ss_modifier = request.user
            branch_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)