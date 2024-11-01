from django.db import models
from django.core.serializers import serialize
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db.models import Max
from organizations.models import branchslist, organizationlst
from supplier_setup.models import suppliers
from store_setup.models import store
from item_setup.models import items
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class purchase_order_list(models.Model):
    po_id = models.BigAutoField(primary_key=True, default=2210000000000, editable=False)
    po_no = models.CharField(max_length=15, editable=False)
    transaction_date = models.DateField(null=True, blank=True)
    expected_date = models.DateField(null=True, blank=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2polist', on_delete=models.DO_NOTHING, editable=False)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2polist', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2polist', on_delete=models.DO_NOTHING)
    is_credit = models.BooleanField(default=False)
    is_cash = models.BooleanField(default=False)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2polist', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    received_date = models.CharField(max_length=50, null=True, blank=True)
    returned_date = models.CharField(max_length=50, null=True, blank=True)
    return_received_date = models.CharField(max_length=50, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_received = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)
    is_return_received = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2is_appr_by', on_delete=models.DO_NOTHING)
    is_received_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2is_rec_by', on_delete=models.DO_NOTHING)
    is_returned_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2is_retu_by', on_delete=models.DO_NOTHING)
    is_return_received_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2is_retu_rec_by', on_delete=models.DO_NOTHING)
    remarks = models.TextField(max_length=300, default="", blank=True)
    received_remarks = models.TextField(max_length=300, default="", blank=True)
    returned_remarks = models.TextField(max_length=300, default="", blank=True)
    return_received_remarks = models.TextField(max_length=300, default="", blank=True)
    dis_percentance = models.IntegerField(null=True, blank=True)
    vat_percentance = models.IntegerField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2polist', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1101000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2polist', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=120950000000, editable=False)

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.id_org_id and self.branch_id_id:
                try:
                    # Get the maximum existing po_id and increment by 1
                    latest_po_id = purchase_order_list.objects.aggregate(Max('po_id'))['po_id__max']
                    if latest_po_id is not None:
                        self.po_id = latest_po_id + 1
                    else:
                        self.po_id = 2210000000000  # Initial value if no records exist

                    # Set the po_no to "R" followed by current date and a unique number
                    current_date = datetime.now().strftime("%Y%m%d")
                    latest_po_no = purchase_order_list.objects.filter(
                        id_org=self.id_org_id, 
                        branch_id=self.branch_id_id, 
                        po_no__startswith=f"R{current_date}"
                    ).aggregate(Max('po_no'))['po_no__max']

                    if latest_po_no is not None:
                        # Extract the last 4 digits of the po_no and increment
                        latest_number = int(latest_po_no[-4:]) + 1
                        po_no_str = str(latest_number).zfill(4)
                    else:
                        po_no_str = '0001'

                    self.po_no = f"R{current_date}{po_no_str}"

                    # Update session fields
                    user_session = purchase_order_list.objects.latest('ss_created_session')
                    modifier_session = purchase_order_list.objects.latest('ss_modified_session')

                    self.ss_created_session = user_session.ss_created_session + 1
                    self.ss_modified_session = modifier_session.ss_modified_session + 1

                except purchase_order_list.DoesNotExist:
                    pass

        super().save(*args, **kwargs)
        

    def __str__(self):
        return str(self.po_id)
    


class purchase_orderdtls(models.Model):
    podtl_id = models.BigAutoField(primary_key=True, default=3311000000000, editable=False)
    po_id = models.ForeignKey(purchase_order_list, null=True, blank=True, related_name='po_id2podtls', on_delete=models.DO_NOTHING, editable=False)
    transaction_date = models.DateField(null=True, blank=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2podtls', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2podtls', on_delete=models.DO_NOTHING, editable=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    order_qty = models.FloatField(null=True, blank=True)
    unit_price = models.FloatField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2podtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=3291000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2podtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=312950000000, editable=False)
    
    
    def save(self, *args, **kwargs):
        
        podtl_data = purchase_orderdtls.objects.all()

        if podtl_data.exists() and self._state.adding:
            last_orderdtl = podtl_data.latest('podtl_id')
            user_session = podtl_data.latest('ss_created_session')
            modifier_session = podtl_data.latest('ss_modified_session')
            self.podtl_id = int(last_orderdtl.podtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.podtl_id)