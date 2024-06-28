from django.db import models
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
# Type models
class item_type(models.Model):
    type_id = models.BigAutoField(primary_key=True, default=123020000000, editable=False)
    type_no = models.CharField(max_length=50, null=True, blank=True)
    type_name = models.CharField(max_length=100, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2item_type', on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2item_type', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1231000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2item_type', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112350000000, editable=False)

    def save(self, *args, **kwargs):
        type_data = item_type.objects.all()

        if type_data.exists() and self._state.adding:
            last_order = type_data.latest('type_id')
            user_session = type_data.latest('ss_created_session')
            modifier_session = type_data.latest('ss_modified_session')
            self.type_id = int(last_order.type_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.type_id)

# UoM Models
class item_uom(models.Model):
    item_uom_id = models.BigAutoField(primary_key=True, default=123030000000, editable=False)
    item_uom_no = models.CharField(max_length=50, null=True, blank=True)
    item_uom_name = models.CharField(max_length=100, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2item_uom', on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2item_uom', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1232000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2item_uom', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112360000000, editable=False)

    def save(self, *args, **kwargs):
        uom_data = item_uom.objects.all()

        if uom_data.exists() and self._state.adding:
            last_order = uom_data.latest('item_uom_id')
            user_session = uom_data.latest('ss_created_session')
            modifier_session = uom_data.latest('ss_modified_session')
            self.item_uom_id = int(last_order.item_uom_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.item_uom_id)

# Category Models
class item_category(models.Model):
    category_id = models.BigAutoField(primary_key=True, default=123040000000, editable=False)
    category_no = models.CharField(max_length=50, null=True, blank=True)
    category_name = models.CharField(max_length=100, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2item_category', on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2item_category', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1233000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2item_category', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112360000000, editable=False)

    def save(self, *args, **kwargs):
        category_data = item_category.objects.all()

        if category_data.exists() and self._state.adding:
            last_order = category_data.latest('category_id')
            user_session = category_data.latest('ss_created_session')
            modifier_session = category_data.latest('ss_modified_session')
            self.category_id = int(last_order.category_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.category_id)