from django.db import models
from datetime import datetime
from django.utils import timezone
from pytz import timezone as tz
from store_setup.models import store
from item_setup.models import items, item_supplierdtl
from stock_list.models import stock_lists
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class barcodes(models.Model):
    bar_id = models.BigAutoField(primary_key=True, default=190000000000, editable=False)
    stock_id = models.ForeignKey(stock_lists, null=True, blank=True, related_name='stock_id2barcodes', on_delete=models.DO_NOTHING)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2barcodes', on_delete=models.DO_NOTHING)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2barcodes', on_delete=models.DO_NOTHING)
    barcode_img = models.ImageField(upload_to='barcode_image', max_length=255, null=True, blank=True)
    status = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2barcodes', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1990000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2barcodes', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1999000000000, editable=False)
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = barcodes.objects.latest('bar_id') if barcodes.objects.exists() else None
            last_user_session = barcodes.objects.latest('ss_created_session') if barcodes.objects.exists() else None
            last_modifier_session = barcodes.objects.latest('ss_modified_session') if barcodes.objects.exists() else None

            self.bar_id = last_order.bar_id + 1 if last_order else 190000000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1990000000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 1999000000000

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.bar_id)