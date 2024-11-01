from organizations.models import branchslist, organizationlst
from supplier_setup.models import suppliers, manufacturer
from others_setup.models import item_type, item_uom, item_category
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

# item setup models
class items(models.Model):
    item_id = models.BigAutoField(primary_key=True, default=1233010000000, editable=False)
    item_no = models.CharField(max_length=100, null=True, blank=True)
    item_name = models.CharField(max_length=200, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2items', on_delete=models.DO_NOTHING)
    type_id = models.ForeignKey(item_type, null=True, blank=True, related_name='item_type2items', on_delete=models.DO_NOTHING, editable=False)
    sales_price = models.CharField(max_length=100, null=True, blank=True)
    purchase_price = models.CharField(max_length=100, null=True, blank=True)
    item_uom_id = models.ForeignKey(item_uom, null=True, blank=True, related_name='item_uom2items', on_delete=models.DO_NOTHING, editable=False)
    # manufacturer value in supplier list
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2items', on_delete=models.DO_NOTHING, editable=False)
    category_id = models.ForeignKey(item_category, null=True, blank=True, related_name='item_category2items', on_delete=models.DO_NOTHING, editable=False)
    box_qty = models.CharField(max_length=100, null=True, blank=True)
    re_order_qty = models.IntegerField(null=True, blank=True)
    discount_percentace = models.CharField(max_length=100, null=True, blank=True)
    discount_tk = models.CharField(max_length=100, null=True, blank=True)
    extended_stock = models.IntegerField(null=True, blank=True, default=0)
    is_active = models.BooleanField(default=True)
    is_foreign_flag = models.BooleanField(default=False)
    is_discount_able = models.BooleanField(default=False)
    is_expireable = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2items', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1235000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2items', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=112340000000, editable=False)

    def save(self, *args, **kwargs):
        items_data = items.objects.all()

        if items_data.exists() and self._state.adding:
            last_order = items_data.latest('item_id')
            user_session = items_data.latest('ss_created_session')
            modifier_session = items_data.latest('ss_modified_session')
            self.item_id = int(last_order.item_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.item_id)


# item supplierdtl models
class item_supplierdtl(models.Model):
    supplierdtl_id = models.BigAutoField(primary_key=True, default=1234010000000, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, on_delete=models.DO_NOTHING)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2item_supp', on_delete=models.DO_NOTHING, editable=False)
    quotation_price = models.CharField(max_length=100, null=True, blank=True)
    supp_sales_price = models.CharField(max_length=100, null=True, blank=True)
    supplier_is_active = models.BooleanField(
        default=True, null=True, blank=True)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2item_supplierdtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=12370000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2item_supplierdtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=11238000000000, editable=False)

    def save(self, *args, **kwargs):
        supplierdtl = item_supplierdtl.objects.all()

        if supplierdtl.exists() and self._state.adding:
            last_order = supplierdtl.latest('supplierdtl_id')
            user_session = supplierdtl.latest('ss_created_session')
            modifier_session = supplierdtl.latest('ss_modified_session')
            self.supplierdtl_id = int(last_order.supplierdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.supplierdtl_id)


# class test(models.Model):
#     id = models.AutoField(
#         primary_key=True, default=1234010000000, editable=False)
