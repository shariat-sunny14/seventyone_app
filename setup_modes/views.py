import json
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from organizations.models import organizationlst
from setup_modes.models import UItemplate_setup
from store_setup.models import store
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
@login_required
def storeWiseSetupModeManagerAPI(request):
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

    return render(request, 'setup_modes/setup_modes.html', context)


@login_required
def getUITemplateAPI(request):
    org_id = request.GET.get('org')

    # Fetch the UItemplate_setup object based on the provided org_id
    uitem_data = UItemplate_setup.objects.filter(org_id=org_id).first()

    # Check if the object exists
    if uitem_data:
        # Extract uitemp_name from the UItemplate_setup object
        uitemp_name = uitem_data.uitemp_name

        # Return the uitemp_name in the JsonResponse
        return JsonResponse({'uitemp_name': uitemp_name})
    else:
        # If the UItemplate_setup object doesn't exist for the given org_id
        return JsonResponse({'error': 'UItemplate_setup not found for the provided org_id'}, status=404)


@login_required
def addUpdateUITemplateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST

    try:
        # Validation of input data
        uitemp_name = data.get('uitemp_name')
        org_id = data.get('org')
        is_org_store = data.get('is_org_store', False)
        is_branch_store = data.get('is_branch_store', False)  # Default to False if not present

        if not uitemp_name or not org_id:
            raise ValueError('Invalid input data')

        org_instance = get_object_or_404(organizationlst, org_id=org_id)

        with transaction.atomic():
            # Attempt to get the UItemplate_setup object
            uitemp_data = UItemplate_setup.objects.filter(org_id=org_instance).first()

            if uitemp_data is None:
                # If the UItemplate_setup object doesn't exist, create a new one
                uitemp_data = UItemplate_setup(org_id=org_instance)

            # Update fields in UItemplate_setup
            uitemp_data.uitemp_name = uitemp_name
            uitemp_data.ss_creator = request.user
            uitemp_data.ss_modifier = request.user
            uitemp_data.save()

            # Update fields in all associated store instances
            store_instances = store.objects.filter(org_id=org_instance)
            store_instances.update(is_org_store=is_org_store, is_branch_store=is_branch_store)

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
            resp['data'] = model_to_dict(uitemp_data)  # Optional: Return data if needed

    except ValueError as ve:
        resp['errmsg'] = str(ve)

    return JsonResponse(resp)