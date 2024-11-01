import sys
import json
from datetime import date, datetime
from django.db.models import Q, F, Sum, Prefetch, ExpressionWrapper, fields, FloatField
from django.db import models
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from bank_setup.models import bank_lists
from . models import cash_on_hands, daily_bank_statement
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def bankStatementManagerAPI(request):
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
    return render(request, 'bank_statement/bank_statements/bank_statement_list.html', context)

@login_required()
def getBankStatementListsAPI(request):
    # Retrieve filter parameters from the frontend
    org_id_wise_filter = request.GET.get('org_id')
    branch_id_wise_filter = request.GET.get('branch_id')
    start_date_wise_filter = request.GET.get('start_date')
    end_date_wise_filter = request.GET.get('end_date')

    filter_kwargs = Q()

    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)
    
    if branch_id_wise_filter:  # Exclude branch_id if it's not provided
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)
        
    # Add date range filter conditions if start_date and end_date are provided
    if start_date_wise_filter and end_date_wise_filter:
        start_date = datetime.strptime(start_date_wise_filter, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_wise_filter, '%Y-%m-%d')
        filter_kwargs &= Q(deposit_date__range=(start_date, end_date))

    # Apply dynamic filters to daily_bank_statement queryset
    deposit_data = daily_bank_statement.objects.filter(filter_kwargs).filter(is_bank_statement=True)
    
    # Convert expense data to a list of dictionaries
    depositData = []
    for deposit in deposit_data:
        depositData.append({
            'deposit_id': deposit.deposit_id,
            'bank_name': deposit.bank_id.bank_name if deposit.bank_id else None,
            'account_no': deposit.bank_id.account_no if deposit.bank_id.account_no else None,
            'types_deposit': deposit.types_deposit,
            'pay_methord': deposit.pay_methord,
            'deposit_reason': deposit.deposit_reason,
            'deposit_date': deposit.deposit_date,
            'deposits_amt': deposit.deposits_amt,
        })

    # Return the filtered data as JSON
    return JsonResponse({'deposit_val': depositData})

# add BankStatement modal
@login_required()
def addBankStatementModelManageAPI(request):
    user = request.user

    bank_data = bank_lists.objects.filter(is_active=True, org_id=user.org_id).all()

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
        'bank_data': bank_data,
    }
    return render(request, 'bank_statement/bank_statements/add_bank_statement.html', context)


# Expense add/update view
@login_required()
def addBankStatementAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org_id')
    branch_id = data.get('branch_id')
    bank_id = data.get('banks_name')
    types_deposit = data.get('types_deposits')
    deposits_amt = data.get('deposits_amt')
    pay_methord = data.get('pay_methord')
    deposit_reason = data.get('deposit_reason')
    deposit_date = data.get('deposits_date')

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            bank_instance = bank_lists.objects.get(bank_id=bank_id)

            deposit_data = daily_bank_statement()

            if float(deposits_amt) > 0:
                # Update or set the fields based on request data
                deposit_data.deposits_amt = deposits_amt
                deposit_data.deposit_date = deposit_date
                deposit_data.deposit_reason = deposit_reason
                deposit_data.types_deposit = types_deposit
                deposit_data.pay_methord = pay_methord
                deposit_data.org_id = organization_instance
                deposit_data.branch_id = branch_instance
                deposit_data.bank_id = bank_instance
                deposit_data.is_bank_statement = True
                deposit_data.is_branch_deposit = False
                deposit_data.is_branch_deposit_receive = False
                deposit_data.ss_creator = request.user
                deposit_data.ss_modifier = request.user
                deposit_data.save()

                cash_on_hands_obj, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    defaults={
                        'on_hand_cash': 0,  # Set default to 0 if not exists
                    }
                )
                # Subtract the deposits_amt from on_hand_cash
                cash_on_hands_obj.on_hand_cash -= float(deposits_amt)
                cash_on_hands_obj.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)



# =============================================xxxxx deposit at main branch xxxxx=============================================

@login_required()
def depositInbranchStatementAPI(request):
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
    return render(request, 'bank_statement/deposit_at_main_branch/deposit_at_main_branch_list.html', context)


@login_required()
def getDepositInBranchListsAPI(request):
    # Retrieve filter parameters from the frontend
    org_id_wise_filter = request.GET.get('org_id')
    branch_id_wise_filter = request.GET.get('branch_id')
    start_date_wise_filter = request.GET.get('start_date')
    end_date_wise_filter = request.GET.get('end_date')

    filter_kwargs = Q()

    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)
    
    if branch_id_wise_filter:  # Exclude branch_id if it's not provided
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)
        
    # Add date range filter conditions if start_date and end_date are provided
    if start_date_wise_filter and end_date_wise_filter:
        start_date = datetime.strptime(start_date_wise_filter, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_wise_filter, '%Y-%m-%d')
        filter_kwargs &= Q(deposit_date__range=(start_date, end_date))

    # Apply dynamic filters to daily_bank_statement queryset
    deposit_data = daily_bank_statement.objects.filter(filter_kwargs).filter(is_branch_deposit=True)
    
    # Convert expense data to a list of dictionaries
    depositData = []
    for deposit in deposit_data:
        depositData.append({
            'deposit_id': deposit.deposit_id,
            'sub_branch': deposit.sub_branch_id.branch_name,
            'main_branch': deposit.main_branch_id.branch_name,
            'types_deposit': deposit.types_deposit,
            'pay_methord': deposit.pay_methord,
            'deposit_reason': deposit.deposit_reason,
            'deposit_date': deposit.deposit_date,
            'deposits_amt': deposit.deposits_amt,
        })

    # Return the filtered data as JSON
    return JsonResponse({'deposit_val': depositData})


# add deposit at main branch Statement modal
@login_required()
def addDepositAtMainBranchModelAPI(request):
    user = request.user

    sub_branch_data = branchslist.objects.filter(is_active=True, is_sub_branch=True).all()
    main_branch_data = branchslist.objects.filter(is_active=True, is_main_branch=True).all()

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
        'sub_branch_data': sub_branch_data,
        'main_branch_data': main_branch_data,
    }
    return render(request, 'bank_statement/deposit_at_main_branch/add_deposit_at_main_branch_model.html', context)


# save deposit at main branch to sub branch
@login_required()
def saveDepositAtMainBranchStatementAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org_id')
    sub_branch_id = data.get('sub_branch')
    main_branch_id = data.get('main_branch')
    types_deposit = data.get('types_deposits')
    deposits_amt = data.get('deposits_amt')
    pay_methord = data.get('pay_methord')
    deposit_reason = data.get('deposit_reason')
    deposit_date = data.get('deposits_date')

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            sub_branch_instance = branchslist.objects.get(branch_id=sub_branch_id)
            main_branch_instance = branchslist.objects.get(branch_id=main_branch_id)

            deposit_data = daily_bank_statement()

            if float(deposits_amt) > 0:
                # Update or set the fields based on request data
                deposit_data.deposits_amt = deposits_amt
                deposit_data.deposit_date = deposit_date
                deposit_data.deposit_reason = deposit_reason
                deposit_data.types_deposit = types_deposit
                deposit_data.pay_methord = pay_methord
                deposit_data.org_id = organization_instance
                deposit_data.branch_id = sub_branch_instance
                deposit_data.sub_branch_id = sub_branch_instance
                deposit_data.main_branch_id = main_branch_instance
                deposit_data.is_bank_statement = False
                deposit_data.is_branch_deposit = True
                deposit_data.is_branch_deposit_receive = False
                deposit_data.ss_creator = request.user
                deposit_data.ss_modifier = request.user
                deposit_data.save()

                cash_on_hands_obj, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=sub_branch_instance,
                    defaults={
                        'on_hand_cash': 0,  # Set default to 0 if not exists
                    }
                )
                # Subtract the deposits_amt from on_hand_cash
                cash_on_hands_obj.on_hand_cash -= float(deposits_amt)
                cash_on_hands_obj.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


# =============================================xxxxx deposit received at sub branch xxxxx=============================================

@login_required()
def depositReceivedInbranchStatementAPI(request):
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
    return render(request, 'bank_statement/deposit_rec_at_sub_branch/deposit_rec_at_sub_branch_list.html', context)


@login_required()
def getDepRecAtSubBranchListAPI(request):
    # Retrieve filter parameters from the frontend
    org_id_wise_filter = request.GET.get('org_id')
    branch_id_wise_filter = request.GET.get('branch_id')
    start_date_wise_filter = request.GET.get('start_date')
    end_date_wise_filter = request.GET.get('end_date')

    filter_kwargs = Q()

    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)
    
    if branch_id_wise_filter:  # Exclude branch_id if it's not provided
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)
        
    # Add date range filter conditions if start_date and end_date are provided
    if start_date_wise_filter and end_date_wise_filter:
        start_date = datetime.strptime(start_date_wise_filter, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_wise_filter, '%Y-%m-%d')
        filter_kwargs &= Q(deposit_date__range=(start_date, end_date))

    # Apply dynamic filters to daily_bank_statement queryset
    deposit_data = daily_bank_statement.objects.filter(filter_kwargs).filter(is_branch_deposit_receive=True)
    
    # Convert expense data to a list of dictionaries
    depositData = []
    for deposit in deposit_data:
        depositData.append({
            'deposit_id': deposit.deposit_id,
            'sub_branch': deposit.sub_branch_id.branch_name,
            'main_branch': deposit.main_branch_id.branch_name,
            'types_deposit': deposit.types_deposit,
            'pay_methord': deposit.pay_methord,
            'deposit_reason': deposit.deposit_reason,
            'deposit_date': deposit.deposit_date,
            'deposits_amt': deposit.deposits_amt,
        })

    # Return the filtered data as JSON
    return JsonResponse({'deposit_val': depositData})


# add deposit received at sub main branch Statement modal
@login_required()
def addDepReceivedAtSubBranchModelAPI(request):
    user = request.user

    sub_branch_data = branchslist.objects.filter(is_active=True, is_sub_branch=True).all()
    main_branch_data = branchslist.objects.filter(is_active=True, is_main_branch=True).all()

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
        'sub_branch_data': sub_branch_data,
        'main_branch_data': main_branch_data,
    }
    return render(request, 'bank_statement/deposit_rec_at_sub_branch/add_dep_rec_at_sub_branch_model.html', context)


# save recieve deposit at sub branch to main branch
@login_required()
def saveReceivedDepositAtmainBranchAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org_id')
    sub_branch_id = data.get('sub_branch')
    main_branch_id = data.get('main_branch')
    types_deposit = data.get('types_deposits')
    deposits_amt = data.get('deposits_amt')
    pay_methord = data.get('pay_methord')
    deposit_reason = data.get('deposit_reason')
    deposit_date = data.get('deposits_date')

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            sub_branch_instance = branchslist.objects.get(branch_id=sub_branch_id)
            main_branch_instance = branchslist.objects.get(branch_id=main_branch_id)

            deposit_data = daily_bank_statement()

            if float(deposits_amt) > 0:
                # Update or set the fields based on request data
                deposit_data.deposits_amt = deposits_amt
                deposit_data.deposit_date = deposit_date
                deposit_data.deposit_reason = deposit_reason
                deposit_data.types_deposit = types_deposit
                deposit_data.pay_methord = pay_methord
                deposit_data.org_id = organization_instance
                deposit_data.branch_id = main_branch_instance
                deposit_data.sub_branch_id = sub_branch_instance
                deposit_data.main_branch_id = main_branch_instance
                deposit_data.is_bank_statement = False
                deposit_data.is_branch_deposit = False
                deposit_data.is_branch_deposit_receive = True
                deposit_data.ss_creator = request.user
                deposit_data.ss_modifier = request.user
                deposit_data.save()

                cash_on_hands_obj, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=main_branch_instance,
                    defaults={
                        'on_hand_cash': 0,  # Set default to 0 if not exists
                    }
                )
                # Subtract the deposits_amt from on_hand_cash
                cash_on_hands_obj.on_hand_cash -= float(deposits_amt)
                cash_on_hands_obj.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)