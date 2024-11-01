import json
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from organizations.models import organizationlst
from django.shortcuts import render
from . models import in_bill_receipts
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
@login_required
def selectBillReceiptManagerAPI(request):
    user = request.user

    # Retrieve organization list based on user privileges
    if user.is_superuser:
        org_list = organizationlst.objects.filter(is_active=True)
    elif user.org_id is not None:
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id)
    else:
        org_list = []

    context = {
        'org_list': org_list,
    }

    return render(request, 'bill_receipt/bill_receipt.html', context)


@login_required
def getReceiptOptionManagerAPI(request):
    org_id = request.GET.get('org_filter')
    
    if org_id:
        try:
            # Fetch the organization to get the org_name
            organization = organizationlst.objects.get(org_id=org_id)
            # Retrieve receipts related to this organization
            receipts = in_bill_receipts.objects.filter(org_id=org_id)
            
            data = [
                {
                    'receipt_id': receipt.receipt_id,
                    'org_name': organization.org_name,  # Use organization instance to get org_name
                    'receipt_name': receipt.receipt_name,
                    'chalan_name': receipt.chalan_name,
                }
                for receipt in receipts
            ]
        except organizationlst.DoesNotExist:
            # If the organization does not exist, return an empty list
            data = []
    else:
        data = []

    return JsonResponse(data, safe=False)


@login_required
def saveSelectBillReceiptAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST

    try:
        # Get the form data
        org_id = data.get('org')
        bill_receipt = data.get('bill_receipt')  # This corresponds to receipt_name
        deliver_chalan = data.get('deliver_chalan')  # This corresponds to chalan_name

        # Fetch the organization instance
        org_instance = get_object_or_404(organizationlst, org_id=org_id)

        with transaction.atomic():
            # Use get_or_create to find the existing record or create a new one
            orgRec_data, created = in_bill_receipts.objects.get_or_create(
                org_id=org_instance,
                defaults={
                    'receipt_name': bill_receipt,  # Use correct field name from the model
                    'chalan_name': deliver_chalan,  # Use correct field name from the model
                    'ss_creator': request.user,
                    'ss_modifier': request.user,
                }
            )

            if not created:
                # Update fields if the record already exists
                orgRec_data.receipt_name = bill_receipt  # Use correct field name
                orgRec_data.chalan_name = deliver_chalan  # Use correct field name
                orgRec_data.ss_modifier = request.user
                orgRec_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully' if not created else 'Created successfully'

    except ValueError as ve:
        resp['errmsg'] = str(ve)
    except Exception as e:
        resp['errmsg'] = f"An error occurred: {str(e)}"

    return JsonResponse(resp)