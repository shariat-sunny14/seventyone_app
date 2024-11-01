import sys
import json
from num2words import num2words
from pickle import FALSE
from datetime import datetime
from django.db.models import Q, Sum, Count, F
from django.db import transaction
from django.db.models import Prefetch
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms.models import model_to_dict
from stock_list.stock_qty import get_available_qty
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from item_setup.models import items
from organizations.models import branchslist, organizationlst
from stock_list.models import in_stock
from store_setup.models import store
from drivers_setup.models import drivers_list
from registrations.models import in_registrations
from deliver_chalan.models import delivery_Chalan_list, delivery_Chalandtl_list
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.
@login_required()
def postOrderUpdateManageAPI(request):
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

    return render(request, 'post_order_update/post_order_update.html', context)


@login_required()
def getPostorderUpdateInvoiceDtlsAPI(request):
    inv_id = request.GET.get('inv_id')

    try:
        # Check if the invoice exists
        if not invoice_list.objects.filter(inv_id=inv_id).exists():
            return JsonResponse({'status': 'unsuccess', 'errmsg': 'Invoice not found'})
        
        invoice = invoice_list.objects.get(inv_id=inv_id)
        invoice_details = invoicedtl_list.objects.filter(inv_id=inv_id)
        payment_details = payment_list.objects.filter(inv_id=inv_id)
        carrying_details = rent_others_exps.objects.filter(inv_id=inv_id)
        
        # Invoice header details
        invoice_data = {
            'inv_id': invoice.inv_id,
            'invoice_date': invoice.invoice_date,
            'supplier_id': invoice.supplier_id.supplier_id if invoice.supplier_id and invoice.supplier_id.supplier_id else '',
            'reg_id': invoice.reg_id.reg_id if invoice.reg_id and invoice.reg_id.reg_id else '',
            'client_no': invoice.supplier_id.supplier_no if invoice.supplier_id and invoice.supplier_id.supplier_no else '',
            'client_name': invoice.supplier_id.supplier_name if invoice.supplier_id and invoice.supplier_id.supplier_name else '',
            'contact': invoice.supplier_id.phone if invoice.supplier_id and invoice.supplier_id.phone else '',
            'client_address': invoice.supplier_id.address if invoice.supplier_id and invoice.supplier_id.address else '',
            'org_id': invoice.org_id.org_id if invoice.org_id and invoice.org_id.org_id else '',
            'cash_point': invoice.cash_point.store_id if invoice.cash_point and invoice.cash_point.store_id else '',
            'customer_name': invoice.customer_name,
            'road_no': invoice.road_no,
            'address': invoice.address,
            'remarks': invoice.remarks,
            'branchs': invoice.branch_id.branch_id if invoice.branch_id and invoice.branch_id.branch_id else '',
            'gender': invoice.gender,
            'mobile_number': invoice.mobile_number,
            'area': invoice.area,
            'driver_id': invoice.driver_id.driver_id if invoice.driver_id and invoice.driver_id.driver_id else '',
            'driver_name': invoice.driver_name,
            'driver_mobile': invoice.driver_mobile,
            'emergency_person': invoice.emergency_person,
            'emergency_phone': invoice.emergency_phone,
            'house_no': invoice.house_no,
            'sector_no': invoice.sector_no,
            'floor_no': invoice.floor_no,
            'is_general_bill': invoice.is_general_bill,
            'is_b2b_clients': invoice.is_b2b_clients,
            'is_non_register': invoice.is_non_register,
            'is_register': invoice.is_register,
            'is_carrcost_notapp': invoice.is_carrcost_notapp,
            'is_modified_item': invoice.is_modified_item,
        }

        # Invoice detail lines
        invoice_details_data = []
        total_gross_disc = 0
        total_vat_tax = 0
        grand_sales_rates = 0
        grand_vat_tax_amt = 0
        tota_can_qty = 0

        for detail in invoice_details:

            can_qty = detail.is_cancel_qty
            tota_can_qty += can_qty

            if tota_can_qty > 0:
                return JsonResponse({'success': False, 'errmsg': 'Not Allow!. This Invoice / Invoice Item Already Canceled.'})
            
            gross_disc = detail.gross_dis
            total_gross_disc += round(gross_disc, 1)

            total_qty = detail.qty - detail.is_cancel_qty

            total_sales_rates = (detail.sales_rate * total_qty) - detail.item_w_dis
            grand_sales_rates += round(total_sales_rates, 0)

            vat_tax = detail.gross_vat_tax
            total_vat_tax += round(vat_tax, 0)

            grand_vat_tax = total_vat_tax * 100
            grand_vat_tax = round(grand_vat_tax, 0)

            if grand_sales_rates != 0:
                grand_vat_tax_amt = (grand_vat_tax / grand_sales_rates)

            item_modify = detail.inv_id.is_modified_item

            if item_modify:
                item_name = detail.item_name if detail.item_name else ''
            else:
                item_name = detail.item_id.item_name if detail.item_id and detail.item_id.item_name else ''

            available_qty = get_available_qty(detail.item_id.item_id, detail.store_id.store_id, detail.item_id.org_id.org_id)
            invoice_details_data.append({
                'invdtl_id': detail.invdtl_id,
                'item_id': detail.item_id.item_id,
                're_order_qty': detail.item_id.re_order_qty,
                'store_id': detail.store_id.store_id,
                'item_no': detail.item_id.item_no if detail.item_id and detail.item_id.item_no else '',
                'item_name': item_name,
                'item_type': detail.item_id.type_id.type_name if detail.item_id and detail.item_id.type_id.type_name else '',
                'item_uom': detail.item_id.item_uom_id.item_uom_name if detail.item_id and detail.item_id.item_uom_id.item_uom_name else '',
                'item_supplier': detail.item_id.supplier_id.supplier_name if detail.item_id.supplier_id and detail.item_id.supplier_id.supplier_name else '',
                'extended_stock': detail.item_id.extended_stock if detail.item_id and detail.item_id.extended_stock else 0,
                'stock_qty': available_qty,
                'sales_qty': detail.qty,
                'is_cancel_qty': detail.is_cancel_qty,
                'item_price': detail.sales_rate,
                'item_w_dis': detail.item_w_dis,
                'total_gross_disc': total_gross_disc,
                'gross_vat_tax': detail.gross_vat_tax,
                'grand_vat_tax_amt': grand_vat_tax_amt,
            })
        
        payment_details_data = []

        # Aggregate the sums of payments based on collection modes
        collection_amt = payment_details.filter(collection_mode="1").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        due_collection_amt = payment_details.filter(collection_mode="2").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0
        adjust_collection_amt = payment_details.filter(collection_mode="4").aggregate(pay_amt_sum=Sum('pay_amt'))['pay_amt_sum'] or 0

        # Calculate the total payment amount for each payment record
        total_payment_amt = collection_amt + due_collection_amt + adjust_collection_amt

        for payment in payment_details:
            payment_details_data.append({
                'pay_id': payment.pay_id,
                'pay_amt': total_payment_amt,  # Use the total sum for all payments
            })

        carrying_details_data = []

        for carrying in carrying_details:
            carrying_details_data.append({
                'other_exps_id': carrying.other_exps_id,
                'is_seller': carrying.is_seller,
                'is_buyer': carrying.is_buyer,
                'other_exps_amt': carrying.other_exps_amt,
            })

        return JsonResponse({
            'invoice': invoice_data,
            'details': invoice_details_data,
            'payments': payment_details_data,
            'carryings': carrying_details_data,
            'success': True
        })

    except invoice_list.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
    

@login_required()
def updateSavePosBillAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Update Failed'}
    data = request.POST

    inv_id = data.get('inv_id')
    cash_point = data.get('cash_point')
    org_id = data.get('org')
    branch_id = data.get('branchs')
    supplier_id = data.get('supplier_id')
    reg_id = data.get('reg_id')
    driver_id = data.get('driver_id')
    driver_name = data.get('driver_name')
    driver_mobile = data.get('driver_mobile')
    general_bill = data.get('general_bill', False)
    b2b_clients = data.get('b2b_clients', False)
    non_register = data.get('non_register', False)
    register = data.get('register', False)
    seller = data.get('seller', False)
    buyer = data.get('buyer', False)
    notapp_carr_cost = data.get('notapp_carr_cost', False)
    is_modified_items = data.get('is_modified_items', False)
    other_exps_amt = data.get('rent_other_expense', '').strip()

    try:
        with transaction.atomic():
            # Fetch related instances
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            cash_point_instance = store.objects.get(store_id=cash_point)

            if supplier_id:
                suppliers_instance = suppliers.objects.get(supplier_id=supplier_id)
            else:
                suppliers_instance = None
            
            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None

            if driver_id:
                drivers_instance = drivers_list.objects.get(driver_id=driver_id)
            else:
                drivers_instance = None

            # Check if inv_id exists, update if it does, otherwise return an error
            if inv_id:
                try:
                    invoice = invoice_list.objects.get(inv_id=inv_id)
                except invoice_list.DoesNotExist:
                    resp['errmsg'] = 'Invoice Not Found!'
                    return JsonResponse(resp)
                
                # Try to fetch the chalan, skip if not found
                try:
                    chalan = delivery_Chalan_list.objects.get(inv_id=inv_id)
                except delivery_Chalan_list.DoesNotExist:
                    chalan = None  # Proceed without blocking if not found
                
                # Update existing invoice
                invoice.org_id = organization_instance
                invoice.branch_id = branch_instance
                invoice.supplier_id = suppliers_instance
                invoice.reg_id = reg_instance
                invoice.driver_id = drivers_instance
                invoice.driver_name = driver_name
                invoice.driver_mobile = driver_mobile
                invoice.cash_point = cash_point_instance
                invoice.is_general_bill = general_bill
                invoice.is_b2b_clients = b2b_clients
                invoice.is_non_register = non_register
                invoice.is_register = register
                invoice.is_carrcost_notapp = notapp_carr_cost
                invoice.is_modified_item = is_modified_items
                invoice.is_update = True
                invoice.customer_name = data['customer_name']
                invoice.gender = data.get('gender', '')
                invoice.mobile_number = data['mobile_number']
                invoice.house_no = data['house_no']
                invoice.road_no = data['road_no']
                invoice.sector_no = data['sector_no']
                invoice.area = data['area']
                invoice.floor_no = data['floor_no']
                invoice.address = data['address']
                invoice.emergency_person = data['emergency_person']
                invoice.emergency_phone = data['emergency_phone']
                invoice.remarks = data['remarks']
                invoice.ss_modifier = request.user
                invoice.save()

                invoice_id = invoice.inv_id
                is_carrcost_notapp = invoice.is_carrcost_notapp

                # delivery_Chalan_list modify # Update Chalan if found
                if chalan:
                    chalan.is_modified_item = is_modified_items
                    chalan.ss_modifier = request.user
                    chalan.save()

                # Process invoicedtl_list and in_stock models
                item_data = list(zip(
                    request.POST.getlist('item_id[]'),
                    request.POST.getlist('store_id[]'),
                    request.POST.getlist('sales_qty[]'),
                    request.POST.getlist('item_price[]'),
                    request.POST.getlist('item_w_dis[]'),
                    request.POST.getlist('gross_dis[]'),
                    request.POST.getlist('gross_vat_tax[]'),
                    request.POST.getlist('item_names[]'),
                ))

                for item_id, store_id, qty, price, w_dis, dis, vat_tax, item_name in item_data:
                    item_instance = items.objects.get(item_id=item_id)
                    store_instance = store.objects.get(store_id=store_id)

                    # Check if 'is_modified_items' is set and if the item_name is not empty or None
                    if is_modified_items == "1":
                        itemName = item_name  # Use the provided item name if it's valid
                    else:
                        itemName = None  # Save as NULL if the item name is not provided or empty

                    qty = float(qty) # if '.' in qty else int(qty)

                    # Get or create the invoice detail
                    inv_detail, created = invoicedtl_list.objects.get_or_create(
                        inv_id=invoice,
                        item_id=item_instance,
                        store_id=store_instance
                    )

                    # # Adjust stock **only if updating an existing record**
                    # if not created:
                    #     # Existing record: Adjust stock based on quantity difference
                    #     previous_qty = inv_detail.qty

                    #     if previous_qty > qty:
                    #         total_qty = previous_qty - qty
                    #         # Increase stock
                    #         in_stock.objects.filter(item_id=item_instance, store_id=store_instance).update(
                    #             stock_qty=F('stock_qty') + total_qty
                    #         )
                    #     elif previous_qty < qty:
                    #         total_qty = qty - previous_qty
                    #         # Decrease stock
                    #         in_stock.objects.filter(item_id=item_instance, store_id=store_instance).update(
                    #             stock_qty=F('stock_qty') - total_qty
                    #         )

                    # Update or create the invoice detail with new data
                    inv_detail.item_name = itemName
                    inv_detail.qty = qty
                    inv_detail.sales_rate = price
                    inv_detail.item_w_dis = w_dis
                    inv_detail.gross_dis = dis
                    inv_detail.gross_vat_tax = vat_tax
                    inv_detail.ss_modifier = request.user
                    inv_detail.save()

                # Handle rent_others_exps model
                # Logic to handle rent_others_exps based on notapp_carr_cost value
                if notapp_carr_cost == "1":
                    # Delete rent_others_exps record if notapp_carr_cost is 1
                    rent_others_exps.objects.filter(inv_id=invoice).delete()
                else:
                    # Create or update rent_others_exps record if notapp_carr_cost is 0
                    rent_other_exps, created = rent_others_exps.objects.update_or_create(
                        inv_id=invoice,
                        org_id=organization_instance,
                        branch_id=branch_instance,
                        defaults={
                            'is_seller': seller,
                            'is_buyer': buyer,
                            'other_exps_reason': 'Carrying Cost',
                            'other_exps_amt': other_exps_amt,
                            'ss_creator': request.user,
                            'ss_modifier': request.user,
                        }
                    )

                resp['status'] = 'success'
                resp['invoice_id'] = invoice_id
                resp['is_carrcost_notapp'] = is_carrcost_notapp
            else:
                # inv_id is not provided or invalid, return an error without creating a new invoice
                resp['msg'] = 'Invoice ID is missing or invalid!'
                return JsonResponse(resp)

    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)



@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def deleteItemInvoiceDtlsAPI(request, invdtl_id):
    if request.method == 'DELETE':
        try:
            # Get the invoicedtl_list instance using invdtl_id
            invoice_DtlID = invoicedtl_list.objects.get(invdtl_id=invdtl_id)

            # Check if the invoice item is already cancelled
            if invoice_DtlID.is_cancel_qty > 0:  # or use a specific value comparison as needed
                return JsonResponse({'success': False, 'errmsg': 'Not Allowed! This Invoice / Invoice Item is already cancelled.'})

            # Get all the matching chalan details
            chalan_DtlIDs = delivery_Chalandtl_list.objects.filter(invdtl_id=invdtl_id)

            tot_del_qty = 0  # Initialize total delivery quantity

            # Loop through the matching delivery_Chalandtl_list entries
            for chalan_DtlID in chalan_DtlIDs:
                del_qty = chalan_DtlID.deliver_qty
                tot_del_qty += float(del_qty)  # Accumulate the total delivery quantity

                # Get the item and store related to the current chalan detail
                item_instance = chalan_DtlID.item_id
                store_instance = chalan_DtlID.deliver_store

                # Get or create the in_stock record for this item and store
                stock, created = in_stock.objects.get_or_create(
                    item_id=item_instance,
                    store_id=store_instance,
                    defaults={'stock_qty': 0}  # Default stock_qty if the record is newly created
                )

                # Update the stock quantity (increase by the cancelled invoice quantity)
                stock.stock_qty = F('stock_qty') + del_qty
                stock.save()

                # Refresh the stock instance to ensure the correct value after updating
                stock.refresh_from_db()

                # Delete the current chalan_DtlID entry
                chalan_DtlID.delete()

            # Finally, delete the invoicedtl_list entry after processing all related chalan details
            invoice_DtlID.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        except invoicedtl_list.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'item invoice dtl id {invdtl_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Error occurred while deleting: {str(e)}'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})