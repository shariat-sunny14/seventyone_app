import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.forms import formset_factory
from django.db.models import Q
from django.db import transaction, IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from .forms import ItemSetupForm, ItemSupplierdtlForm
from . models import items, item_supplierdtl
from others_setup.models import item_type, item_uom, item_category
from supplier_setup.models import suppliers, manufacturer
from django.contrib import messages
from django.contrib.auth import get_user_model
User = get_user_model()


# items views
@login_required()
def item_setupAPI(request):
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

    supplier_list = suppliers.objects.filter(is_active=True, org_id__in=org_list, manufacturer_flag=3)
    
    context_item = {
        'org_list': org_list,
        'supplier_list': supplier_list,
    }

    return render(request, 'item_setup/item_setup.html', context_item)


@login_required()
def getItemTypeListAPI(request):
    if request.method == 'GET':
        user = request.user
        org_id = request.GET.get('org_id', None)

        if user.is_superuser:
            # Superuser can see all branches of the selected organization
            if org_id:
                itype_options = item_type.objects.filter(is_active=True, org_id=org_id).values('type_id', 'type_no', 'type_name')
            else:
                itype_options = []
        elif user.org_id:
            itype_options = item_type.objects.filter(is_active=True, org_id=user.org_id).values('type_id', 'type_no', 'type_name')
            
        else:
            itype_options = []

        return JsonResponse({'itype_list': list(itype_options)})
    return JsonResponse({'error': 'Invalid request'})


@login_required()
def getItemUoMListAPI(request):
    if request.method == 'GET':
        user = request.user
        org_id = request.GET.get('org_id', None)

        if user.is_superuser:
            # Superuser can see all branches of the selected organization
            if org_id:
                iuom_options = item_uom.objects.filter(is_active=True, org_id=org_id).values('item_uom_id', 'item_uom_no', 'item_uom_name')
            else:
                iuom_options = []
        elif user.org_id:
            iuom_options = item_uom.objects.filter(is_active=True, org_id=user.org_id).values('item_uom_id', 'item_uom_no', 'item_uom_name')
            
        else:
            iuom_options = []

        return JsonResponse({'iuom_list': list(iuom_options)})
    return JsonResponse({'error': 'Invalid request'})


@login_required()
def getItemCategoryListAPI(request):
    if request.method == 'GET':
        user = request.user
        org_id = request.GET.get('org_id', None)

        if user.is_superuser:
            # Superuser can see all branches of the selected organization
            if org_id:
                icat_options = item_category.objects.filter(is_active=True, org_id=org_id).values('category_id', 'category_no', 'category_name')
            else:
                icat_options = []
        elif user.org_id:
            icat_options = item_category.objects.filter(is_active=True, org_id=user.org_id).values('category_id', 'category_no', 'category_name')
            
        else:
            icat_options = []

        return JsonResponse({'icat_list': list(icat_options)})
    return JsonResponse({'error': 'Invalid request'})


@login_required()
def getManufacturerListAPI(request):
    if request.method == 'GET':
        user = request.user
        org_id = request.GET.get('org_id', None)

        if user.is_superuser:
            # Superuser can see all manufacturers of the selected organization
            if org_id:
                manu_options = suppliers.objects.filter(is_active=True, manufacturer_flag=3, org_id=org_id).values('supplier_id', 'supplier_no', 'supplier_name')
            else:
                manu_options = []
        elif user.org_id:
            manu_options = suppliers.objects.filter(is_active=True, manufacturer_flag=3, org_id=user.org_id).values('supplier_id', 'supplier_no', 'supplier_name')
        else:
            manu_options = []

        return JsonResponse({'manu_list': list(manu_options)})
    return JsonResponse({'error': 'Invalid request'})


@login_required()
def getSupplierListAPI(request):
    if request.method == 'GET':
        user = request.user
        org_id = request.GET.get('org_id', None)

        if user.is_superuser:
            # Superuser can see all manufacturers of the selected organization
            if org_id:
                supp_options = suppliers.objects.filter(is_active=True, supplier_flag=2, org_id=org_id).values('supplier_id', 'supplier_no', 'supplier_name')
            else:
                supp_options = []
        elif user.org_id:
            supp_options = suppliers.objects.filter(is_active=True, supplier_flag=2, org_id=user.org_id).values('supplier_id', 'supplier_no', 'supplier_name')
        else:
            supp_options = []

        return JsonResponse({'supp_list': list(supp_options)})
    return JsonResponse({'error': 'Invalid request'})
    

@login_required()
def get_items(request):
    option = request.GET.get('option')
    search_query = request.GET.get('search_query', '')
    org_id_wise_filter = request.GET.get('org_filter')
    manuf_wise_filter = request.GET.get('manuf_filter')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if search_query is not empty
    if search_query:
        filter_kwargs |= Q(item_name__icontains=search_query) | Q(item_no__icontains=search_query)

    # Add org_id and branch_id filter conditions
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)
    
    # Add manufacturer filter condition, excluding value "1" which means all manufacturers
    if manuf_wise_filter and manuf_wise_filter != '1':
        filter_kwargs &= Q(supplier_id=manuf_wise_filter)

    # Add is_active filter condition based on store option
    if option == 'true':
        filter_kwargs &= Q(is_active=True)
    elif option == 'false':
        filter_kwargs &= Q(is_active=False)

    # Filter the items directly and retrieve values
    items_data = items.objects.filter(filter_kwargs).values(
        'item_id', 'item_no', 'item_name', 'org_id__org_name', 'is_active'
    )

    # Pagination
    page_number = request.GET.get('page')
    paginator = Paginator(items_data, 500)  # Change '100' to your desired page size

    try:
        paginated_data = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = paginator.page(paginator.num_pages)

    return JsonResponse({
        'data': list(paginated_data),
        'total_pages': paginator.num_pages,
        'current_page': paginated_data.number
    })



# items add
@login_required()
def item_addAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    item_id = data.get('item_id')
    
    try:
        with transaction.atomic():
            type_id = data.get('item_type_name')
            item_uom_id = data.get('uom_name')
            category_id = data.get('category_name')
            supplier_id = data.get('manufacturer_name')
            org_id = data.get('org')

            # Fetch instances of related models
            item_type_instance = item_type.objects.get(type_id=type_id)
            uom_id_instance = item_uom.objects.get(item_uom_id=item_uom_id)
            category_id_instance = item_category.objects.get(category_id=category_id)
            manufac_instance = suppliers.objects.get(supplier_id=supplier_id)
            org_instance = organizationlst.objects.get(org_id=org_id)

            # Check if item_id is provided for an update or add operation
            if item_id and item_id.isnumeric() and int(item_id) > 0:
                # This is an update operation
                item_data = items.objects.get(item_id=item_id)

                # Check if the provided item_no or item_name already exists for other items
                checkitem_no = items.objects.exclude(item_id=item_id).filter(Q(item_no=data.get('item_no')) & Q(org_id=org_instance)).exists()
                checkitem_name = items.objects.exclude(item_id=item_id).filter(Q(item_name=data.get('item_name')) & Q(org_id=org_instance)).exists()

                if checkitem_no:
                    return JsonResponse({'success': False, 'errmsg': 'Item No. Already Exists'})
                elif checkitem_name:
                    return JsonResponse({'success': False, 'errmsg': 'Item Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided item_no or item_name already exists for other items
                checkitem_no = items.objects.filter(Q(item_no=data.get('item_no')) & Q(org_id=org_instance)).exists()
                checkitem_name = items.objects.filter(Q(item_name=data.get('item_name')) & Q(org_id=org_instance)).exists()

                if checkitem_no:
                    return JsonResponse({'success': False, 'errmsg': 'Item No. Already Exists'})
                elif checkitem_name:
                    return JsonResponse({'success': False, 'errmsg': 'Item Name Already Exists'})
                
                # This is an add operation
                item_data = items()

            extended_stock = data.get('extended_stock')

            # Update or set the fields based on request data
            item_data.item_no = data.get('item_no')
            item_data.item_name = data.get('item_name')
            item_data.org_id = org_instance
            item_data.type_id = item_type_instance
            item_data.sales_price = data.get('sales_price')
            item_data.purchase_price = data.get('purchase_price')
            item_data.item_uom_id = uom_id_instance
            item_data.supplier_id = manufac_instance
            item_data.category_id = category_id_instance
            item_data.box_qty = data.get('box_qty')
            item_data.re_order_qty = data.get('re_order_qty')
            item_data.discount_percentace = data.get('discount_percentace')
            item_data.discount_tk = data.get('discount_tk')
            item_data.is_active = data.get('is_active', 0)
            item_data.is_foreign_flag = data.get('is_foreign_flag', 0)
            item_data.is_discount_able = data.get('is_discount_able', 0)
            item_data.is_expireable = data.get('is_expireable', 0)
            item_data.extended_stock = extended_stock if extended_stock else None
            item_data.ss_creator=request.user
            item_data.ss_modifier = request.user
            item_data.save()

            # Clear existing supplier details for the item (if it's an update)
            if item_id:
                item_supplierdtl.objects.filter(item_id=item_data).delete()

            # Update or create supplier details
            supplier_id = data.getlist('supplier_ids[]')
            quotation_price = data.getlist('quotation_prices[]')
            supp_sales_price = data.getlist('supp_sales_prices[]')
            supplier_is_active = data.getlist('supplier_is_actives[]')


            # Get the list of supplier_is_active values and set them to 0 if not present in the form data
            # [int(data.get(f'supplier_is_actives[{i}]', 0)) for i in range(len(supplier_no))]

            for supplier_id, q_price, s_price, is_active_supp in zip(supplier_id, quotation_price, supp_sales_price, supplier_is_active):
                supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
                item_supplierdata = item_supplierdtl(
                    item_id=item_data,
                    supplier_id=supplier_instance,
                    quotation_price=q_price,
                    supp_sales_price=s_price,
                    supplier_is_active=is_active_supp,
                    ss_creator=request.user,
                    ss_modifier=request.user
                )
                item_supplierdata.save()

            resp['success'] = True
            resp['msg'] = 'Item saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getItemListAPI(request, item_id):

    try:
        item_list = get_object_or_404(items, item_id=item_id)
        item_supplier = item_supplierdtl.objects.filter(item_id=item_id)

        item_dtls = []
        item_supplierDtl = []

        item_dtls.append({
            'item_id': item_list.item_id,
            'item_no': item_list.item_no,
            'item_name': item_list.item_name,
            'org_name': item_list.org_id.org_name if item_list.org_id else None,
            'item_type_no': item_list.type_id.type_no,
            'item_type_name': item_list.type_id.type_id,
            'type_name': item_list.type_id.type_name,
            'sales_price': item_list.sales_price,
            'purchase_price': item_list.purchase_price,
            'uom_name': item_list.item_uom_id.item_uom_id,
            'item_uom_name': item_list.item_uom_id.item_uom_name,
            'manufacturer_no': item_list.supplier_id.supplier_no,
            'manufacturer_name': item_list.supplier_id.supplier_id,
            'category_no': item_list.category_id.category_no if item_list.category_id else None,
            'category_name': item_list.category_id.category_id if item_list.category_id else None,
            'box_qty': item_list.box_qty,
            're_order_qty': item_list.re_order_qty,
            'discount_percentace': item_list.discount_percentace,
            'discount_tk': item_list.discount_tk,
            'is_active': item_list.is_active,
            'is_foreign_flag': item_list.is_foreign_flag,
            'is_discount_able': item_list.is_discount_able,
            'is_expireable': item_list.is_expireable,
            'extended_stock': item_list.extended_stock,
        })

        for supplier in item_supplier:
            item_supplierDtl.append({
                'supplierdtl_id': supplier.supplierdtl_id,
                'supplier_id': supplier.supplier_id.supplier_id,
                'supplier_no': supplier.supplier_id.supplier_no,
                'supplier_name': supplier.supplier_id.supplier_name,
                'quotation_price': supplier.quotation_price,
                'supp_sales_price': supplier.supp_sales_price,
                'supplier_is_active': supplier.supplier_is_active,
            })

        context = {
            'item_dtls': item_dtls,
            'item_supplierDtl': item_supplierDtl,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
@login_required()
def deleteSupplierAPI(request, supplierdtl_id):
    if request.method == 'DELETE':
        try:
            # Get the supplier instance using supplierdtl_id
            del_supplier = item_supplierdtl.objects.get(supplierdtl_id=supplierdtl_id)
            del_supplier.delete()

            return JsonResponse({'success': True, 'msg': f'Successfully deleted'})
        except item_supplierdtl.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'Supplier Details ID {supplierdtl_id} Not Found.'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})


@login_required()
def demoApi(request):

    return render(request, 'item_setup/demo.html')