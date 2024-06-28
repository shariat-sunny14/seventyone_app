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
from organizations.models import organizationlst
from .models import departmentlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def departmentSetupAPI(request):

    # Assuming 'country' is a variable representing a lookup code or value
    district_name = 'district'

    districts = lookup_values.objects.filter(identify_code=district_name).all()

    parent_dept = departmentlst.objects.filter(is_parent_dept=True, is_active=True).all()

    context = {
        'districts': districts,
        'parent_dept': parent_dept,
    }
    
    return render(request, 'department_setup/department.html', context)


# organization list show
@login_required()
def get_departments_dataAPI(request):
    deptoption = request.GET.get('deptoption')
    dept_search_query = request.GET.get('dept_search_query', '')

    if deptoption in ['1', 'true', 'false']:
        if deptoption == '1':
            dept_data = departmentlst.objects.filter(Q(dept_name__icontains=dept_search_query) | Q(dept_no__icontains=dept_search_query)).order_by('dept_name')
        elif deptoption == 'true':
            dept_data = departmentlst.objects.filter(Q(is_active=True) & (Q(dept_name__icontains=dept_search_query) | Q(dept_no__icontains=dept_search_query))).order_by('dept_name')
        elif deptoption == 'false':
            dept_data = departmentlst.objects.filter(Q(is_active=False) & (Q(dept_name__icontains=dept_search_query) | Q(dept_no__icontains=dept_search_query))).order_by('dept_name')

        parent_data = [{'dept_id': dept.dept_id, 'dept_no': dept.dept_no, 'dept_name': dept.dept_name, 'is_active': dept.is_active, 'is_parent_dept': dept.is_parent_dept} for dept in dept_data]
        
        # Initialize an empty list to store parent values
        parent_values = []

        for parent in parent_data:
            if parent['is_parent_dept']:  # Check if it's a parent department
                parent_value = {
                    'dept_id': parent['dept_id'],
                    'dept_no': parent['dept_no'],
                    'dept_name': parent['dept_name'],
                    'is_active': parent['is_active'],
                    'details': []
                }

                related_details = departmentlst.objects.filter(parent_dept_id=parent['dept_id']).order_by('dept_name')
                for detail in related_details:
                    parent_value['details'].append({
                        'dept_id': detail.dept_id,
                        'dept_no': detail.dept_no,
                        'dept_name': detail.dept_name,
                        'is_active': detail.is_active
                    })

                parent_values.append(parent_value)  # Append the parent value to the list

        return JsonResponse({'data': parent_values})
    else:
        # If the option is not '1', 'true', or 'false', return an error message
        return JsonResponse({'error': 'Invalid option'})
    

# organization value click to show
@login_required()
def getDepartmentListAPI(request, dept_id):

    try:
        dept_list = get_object_or_404(departmentlst.objects.select_related('parent_dept_id'), dept_id=dept_id)

        dept_Dtls = []

        dept_Dtls.append({
            'dept_id': dept_list.dept_id,
            'dept_no': dept_list.dept_no,
            'is_parent_dept': dept_list.is_parent_dept,
            'is_active': dept_list.is_active,
            'dept_name': dept_list.dept_name,
            'parent_dept_id': dept_list.parent_dept_id.dept_id if dept_list.parent_dept_id else None,  # Get the related dept_id or None
            'alias': dept_list.alias,
            'level': dept_list.level,
            'Report_sl_no': dept_list.Report_sl_no,
            'financebusiness_area': dept_list.financebusiness_area,
            'unitflag_descr': dept_list.unitflag_descr,
            'ipd_dept_flag': dept_list.ipd_dept_flag,
            'opd_dept_flag': dept_list.opd_dept_flag,
            'daycare_flag': dept_list.daycare_flag,
            'clinical_flag': dept_list.clinical_flag,
            'hr_flag': dept_list.hr_flag,
            'film_required': dept_list.film_required,
            'billing_flag': dept_list.billing_flag,
            'dept_bill_activation': dept_list.dept_bill_activation,
            'district': dept_list.district,
            'category': dept_list.category,
            'location': dept_list.location,
            'grade': dept_list.grade,
            'opening_date': dept_list.opening_date,
            'location_type': dept_list.location_type,
            'email': dept_list.email,
            'fax': dept_list.fax,
            'website': dept_list.website,
            'hotline': dept_list.hotline,
            'phone': dept_list.phone,
            'address': dept_list.address,
            'unit_details_descr': dept_list.unit_details_descr,
        })

        context = {
            'dept_Dtls': dept_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# organization add/update view
@login_required()
def department_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    dept_id = data.get('dept_id')

    try:
        with transaction.atomic():
            if dept_id and dept_id.isnumeric() and int(dept_id) > 0:
                dept_data = departmentlst.objects.get(dept_id=dept_id)
                # Check for existing department numbers and names
                check_dept_no = departmentlst.objects.exclude(dept_id=dept_id).filter(dept_no=data.get('dept_no')).exists()
                check_dept_name = departmentlst.objects.exclude(dept_id=dept_id).filter(dept_name=data.get('dept_name')).exists()

                if check_dept_no:
                    return JsonResponse({'success': False, 'errmsg': 'Dept. No. Already Exists'})
                elif check_dept_name:
                    return JsonResponse({'success': False, 'errmsg': 'Dept. Name Already Exists'})
            else:
                # Check for existing department numbers and names for new entries
                check_dept_no = departmentlst.objects.filter(dept_no=data.get('dept_no')).exists()
                check_dept_name = departmentlst.objects.filter(dept_name=data.get('dept_name')).exists()

                if check_dept_no:
                    return JsonResponse({'success': False, 'errmsg': 'Dept. No. Already Exists'})
                elif check_dept_name:
                    return JsonResponse({'success': False, 'errmsg': 'Dept. Name Already Exists'})

                dept_data = departmentlst()

            # Get parent department object
            parent_dept_id = data.get('parent_dept_id')
            parent_dept_obj = get_object_or_404(departmentlst, dept_id=parent_dept_id) if parent_dept_id else None

            # Update or set the fields based on request data
            dept_data.dept_no = data.get('dept_no')
            dept_data.dept_name = data.get('dept_name')
            dept_data.is_parent_dept = data.get('is_parent_dept', 0)
            dept_data.is_active = data.get('is_active', 0)
            dept_data.parent_dept_id = parent_dept_obj
            dept_data.alias = data.get('alias')
            dept_data.level = data.get('level')
            dept_data.Report_sl_no = data.get('Report_sl_no')
            dept_data.financebusiness_area = data.get('financebusiness_area')
            dept_data.unitflag_descr = data.get('unitflag_descr')
            dept_data.ipd_dept_flag = data.get('ipd_dept_flag', 0)
            dept_data.opd_dept_flag = data.get('opd_dept_flag', 0)
            dept_data.daycare_flag = data.get('daycare_flag', 0)
            dept_data.clinical_flag = data.get('clinical_flag', 0)
            dept_data.hr_flag = data.get('hr_flag', 0)
            dept_data.film_required = data.get('film_required', 0)
            dept_data.billing_flag = data.get('billing_flag', 0)
            dept_data.dept_bill_activation = data.get('dept_bill_activation', 0)
            dept_data.district = data.get('district')
            dept_data.category = data.get('category')
            dept_data.location = data.get('location')
            dept_data.grade = data.get('grade')
            dept_data.opening_date = data.get('opening_date') or None
            dept_data.location_type = data.get('location_type')
            dept_data.email = data.get('email')
            dept_data.fax = data.get('fax')
            dept_data.website = data.get('website')
            dept_data.hotline = data.get('hotline')
            dept_data.phone = data.get('phone')
            dept_data.address = data.get('address')
            dept_data.unit_details_descr = data.get('unit_details_descr')
            dept_data.ss_creator = request.user
            dept_data.ss_modifier = request.user
                
            dept_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)