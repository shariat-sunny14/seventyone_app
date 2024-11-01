import io
import os
import re
import json
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.decorators.http import require_POST
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from barcode import Code128, EAN13
from barcode.writer import ImageWriter
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count, Prefetch
from collections import defaultdict
from django.db.models import FloatField
from django.db import transaction
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
    stock_batch = stock_lists.objects.filter(is_approved=True).values(
        'item_batch').annotate(count=Count('item_batch')).order_by('item_batch')

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

    # Base query with store and batch filtering
    base_query = Q(is_approved=True, store_id=selected_store_id)
    if selected_batch_id != "1":
        base_query &= Q(item_batch=selected_batch_id)

    # Apply search query if provided
    if search_query:
        base_query &= (
            Q(item_id__item_no__icontains=search_query) |
            Q(item_id__item_name__icontains=search_query) |
            Q(item_id__type_id__type_name__icontains=search_query) |
            Q(item_id__item_uom_id__item_uom_name__icontains=search_query) |
            Q(item_batch__icontains=search_query) |
            Q(store_id__store_name__icontains=search_query)
        )

    # Use select_related and prefetch_related for optimization
    stock_data = stock_lists.objects.filter(base_query).select_related(
        'item_id', 'store_id'
    ).prefetch_related(
        Prefetch('item_id__item_supplierdtl_set', queryset=item_supplierdtl.objects.select_related('supplier_id'))
    )

    batch_wise_data = []
    for item in stock_data:
        supplier_data = item.item_id.item_supplierdtl_set.first()

        # Get the barcode status safely
        try:
            barcode_status = barcodes.objects.get(stock_id=item)
            status = barcode_status.status  # Access the actual status if found
        except barcodes.DoesNotExist:
            status = False  # Default to False if no barcode found

        batch_wise_item = {
            'item_id': item.item_id.item_id,
            'store_id': item.store_id.store_id,
            'stock_id': item.stock_id,
            'item_no': item.item_id.item_no,
            'item_name': item.item_id.item_name,
            'item_type': item.item_id.type_id.type_name,
            'item_uom': item.item_id.item_uom_id.item_uom_name,
            'item_batch': item.item_batch,
            'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else None,
            'item_Manufacturer': item.item_id.supplier_id.supplier_name,
            'store_name': item.store_id.store_name,
            'status': status,  # Set the actual or default status here
        }

        batch_wise_data.append(batch_wise_item)

    return JsonResponse({'data': batch_wise_data})


@require_POST
@login_required
def generate_barcode(request):
    item_id = request.POST.get('item_id')
    stock_id = request.POST.get('stock_id')  # Retrieve stock_id from the request

    try:
        # Fetch the related stock item using stock_id
        stock_item = stock_lists.objects.filter(item_id=item_id, stock_id=stock_id).first()
        if not stock_item:
            return JsonResponse({
                'message': f'Stock with Item ID: {item_id} and Stock ID: {stock_id} does not exist'
            }, status=400)

        item_name = stock_item.item_id.item_name
        item_batch = stock_item.item_batch

        # Delete existing barcode image if it exists
        existing_barcode_obj = barcodes.objects.filter(
            item_id=stock_item.item_id, stock_id=stock_item.stock_id
        ).first()
        if existing_barcode_obj and existing_barcode_obj.barcode_img:
            existing_barcode_obj.barcode_img.delete()

        # Generate a Code128 barcode number
        barcode_number = f'{item_id}'  # Example: Use item_id and stock_id in Code128 format
        code128 = Code128(barcode_number, writer=ImageWriter())

        # Create an in-memory buffer for the barcode image
        buffer = io.BytesIO()
        code128.write(buffer)
        barcode_img = buffer.getvalue()

        # Prepare the final image with label text
        barcode_image = Image.open(io.BytesIO(barcode_img))
        label_text = f'B: {item_batch}\nN: {item_name}'

        final_image = Image.new(
            'RGB', (barcode_image.width, barcode_image.height + 80), 'white'
        )
        final_image.paste(barcode_image, (0, 0))

        draw = ImageDraw.Draw(final_image)
        font = ImageFont.truetype("arial.ttf", 18)  # Adjust font size if necessary
        draw.text((10, barcode_image.height), label_text, fill='black', font=font)

        # Save the final image to an in-memory file
        img_io = io.BytesIO()
        final_image.save(img_io, format='PNG')
        img_io.seek(0)

        img_file = InMemoryUploadedFile(
            img_io, None, f'{item_id}_barcode.png', 'image/png', img_io.getbuffer().nbytes, None
        )

        # Create or update the barcode object
        barcode_obj, created = barcodes.objects.get_or_create(
            item_id=stock_item.item_id, stock_id=stock_item
        )
        barcode_obj.store_id = stock_item.store_id
        barcode_obj.status = True
        barcode_obj.ss_creator = request.user
        barcode_obj.ss_modifier = request.user
        barcode_obj.barcode_img = img_file
        barcode_obj.save()

        # Get the barcode image URL
        barcode_image_url = barcode_obj.barcode_img.url

        return JsonResponse({
            'message': f'Barcode generated for Item ID: {item_id}',
            'barcode_image_url': barcode_image_url
        })

    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

# ==========================================================================================

@login_required
def get_barcode_status(request, stock_id):
    try:
        barcode = barcodes.objects.get(stock_id=stock_id)
        status = barcode.status  # Replace 'status' with the actual field name in your model
        return JsonResponse({'status': status})
    except barcodes.DoesNotExist:
        return JsonResponse({'status': None})


@login_required
def generate_barcode_bulk(request):
    try:
        # Get selected item and stock IDs as lists
        selected_item_ids = request.POST.getlist('item_id[]')
        selected_stock_ids = request.POST.getlist('stock_id[]')

        mult_barcode_img_urls = []

        # Loop through each item_id and corresponding stock_id
        for item_id, stock_id in zip(selected_item_ids, selected_stock_ids):
            # Convert item_id to an instance of the items model
            item_instance = items.objects.get(item_id=item_id)
            stock_instance = stock_lists.objects.get(stock_id=stock_id)

            # Retrieve stock list object for the given item and stock_id
            item = stock_lists.objects.get(item_id=item_instance, stock_id=stock_instance.stock_id)

            # Retrieve item details
            item_id_code = item_instance.item_id
            item_name = item_instance.item_name
            item_batch = item.item_batch

            # Check if a barcode already exists for the item and delete it if so
            existing_barcode_obj = barcodes.objects.filter(item_id=item_instance).first()
            if existing_barcode_obj:
                existing_barcode_obj.barcode_img.delete()
                existing_barcode_obj.delete()

            # Generate the Code128 barcode
            code128 = Code128(str(item_id_code), writer=ImageWriter())  # No need to pad with zeros
            buffer = io.BytesIO()
            code128.write(buffer)
            barcode_img = buffer.getvalue()

            # Create the final image with label
            barcode_image = Image.open(io.BytesIO(barcode_img))
            label_text = f'B: {item_batch}\nN: {item_name}'
            final_image = Image.new('RGB', (barcode_image.width, barcode_image.height + 80), color='white')
            final_image.paste(barcode_image, (0, 0))

            # Draw text on the final image
            draw = ImageDraw.Draw(final_image)
            font = ImageFont.truetype("arial.ttf", 18)
            draw.text((10, barcode_image.height), label_text, fill='black', font=font)

            # Save final image to in-memory file
            img_io = io.BytesIO()
            final_image.save(img_io, format='PNG')
            img_io.seek(0)

            # Create an InMemoryUploadedFile for the barcode image
            img_file = InMemoryUploadedFile(
                img_io, None, f'{item_id}_barcode.png', 'image/png', img_io.getbuffer().nbytes, None
            )

            # Save the barcode object
            barcode_obj = barcodes.objects.create(
                stock_id=item,
                store_id=item.store_id,
                item_id=item_instance,
                status=True,
                ss_creator=request.user,
                ss_modifier=request.user,
                barcode_img=img_file
            )

            # Append the barcode image URL to the list
            mult_barcode_img_urls.append(barcode_obj.barcode_img.url)

        # Return a JSON response with the image URLs
        return JsonResponse({'mult_barcode_img_urls': mult_barcode_img_urls}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)