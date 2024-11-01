import os
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.decorators.http import require_POST
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO, StringIO
from barcode import Code128
import subprocess
from barcode.writer import ImageWriter
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from collections import defaultdict
from django.db.models import FloatField
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from item_pos.models import invoicedtl_list
from store_setup.models import store
from item_setup.models import items, item_supplierdtl
from stock_list.models import stock_lists
from .models import barcodes
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required
def itemBarcodeManagerAPI(request):
    store_data = store.objects.filter(is_main_store=True).all().order_by('store_name')
    stock_batch = stock_lists.objects.filter(is_approved=True).values('item_batch').annotate(count=Count('item_batch')).order_by('item_batch')

    context = {
        'store_data': store_data,
        'stock_batch': stock_batch,
    }

    return render(request, 'item_barcode/item_barcode.html', context)


@login_required
def getItemWiseBarcodeAPI(request):
    selected_store_id = request.GET.get('store_id')
    selected_batch_id = request.GET.get('item_batch')
    search_query = request.GET.get('search_item_bw')
    
    # Base query to filter stock data based on store and batch
    base_query = Q(is_approved=True, store_id=selected_store_id)
    if selected_batch_id != "1":
        base_query &= Q(item_batch=selected_batch_id)
    
    # Apply search query filter if search_query is present
    if search_query:
        base_query &= (Q(item_id__item_no__icontains=search_query) |
                       Q(item_id__item_name__icontains=search_query) |
                       Q(item_id__type_id__type_name__icontains=search_query) |
                       Q(item_id__item_uom_id__item_uom_name__icontains=search_query) |
                       Q(item_batch__icontains=search_query) |
                       Q(item_id__manufac_id__manufac_name__icontains=search_query) |
                       Q(store_id__store_name__icontains=search_query))
    
    stock_data = stock_lists.objects.filter(base_query)

    batch_wise_data = []

    for item in stock_data:
        item_id = item.item_id.item_id

        # Fetch the supplier's name related to the item_id from item_supplierdtl
        supplier_data = item_supplierdtl.objects.filter(itemdtl_id=item_id).first()
        barcode_status = barcodes.objects.filter(stock_id=item).first()

        # Fetch store_name and item_exp_date related to the stock_lists model
        store_name = item.store_id.store_name if item.store_id else None
        item_exp_date = item.item_exp_date
        item_batch = item.item_batch

        batch_wise_item = {
            'item_id': item.item_id.item_id,
            'store_id': item.store_id.store_id,
            'stock_id': item.stock_id,
            'item_no': item.item_id.item_no,
            'item_name': item.item_id.item_name,
            'item_type': item.item_id.type_id.type_name,
            'item_uom': item.item_id.item_uom_id.item_uom_name,
            'item_batch': item_batch,
            'item_Supplier': supplier_data.supplier_name if supplier_data else None,
            'item_Manufacturer': item.item_id.manufac_id.manufac_name,
            'store_name': store_name,
            'status': barcode_status.status if barcode_status else False,
        }

        batch_wise_data.append(batch_wise_item)

    return JsonResponse({'data': batch_wise_data})


# Path to your .jasper file
# jasper_path = 'media/jasper_report/item_barcode/item_barcode.jasper'

def print_barcode(request):
    if request.method == 'POST':
        item_name = request.POST.get('item_name')  # Retrieve item_name from the request

        # Absolute path to the directory containing jasper files
        jasper_directory = r'C:\Users\User\Music\new work\store projects in django\storeapp\storeapp\media\jasper_report\item_barcode'

        jasper_path = os.path.join(jasper_directory, 'item_barcode.jasper')
        jasper_file = os.path.join(jasper_directory, 'item_barcode.jrxml')
        output_path = os.path.join(jasper_directory, 'item_barcode.pdf')
        print(jasper_path)
        print(jasper_file)
        print(output_path)

        try:
            # Build the command to generate the report using JasperStarter
            jasper_starter_cmd = [
                'jasperstarter',
                'process',
                jasper_file,
                '-o', output_path,
                '-f', 'pdf',
                '-P', f'itemName={item_name}'
            ]

            # Execute the command using subprocess
            subprocess.run(jasper_starter_cmd, check=True)

            # Read the generated PDF file
            with open(output_path, 'rb') as generated_file:
                generated_report = generated_file.read()

            # Return the generated report as an HTTP response
            response = HttpResponse(generated_report, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="report.pdf"'
            return response

        except subprocess.CalledProcessError as e:
            return JsonResponse({'message': f'Error: {e}'}, status=500)

        except FileNotFoundError as e:
            return JsonResponse({'message': str(e)}, status=404)

    return JsonResponse({'message': 'Invalid request'}, status=400)