from django.db import models
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class store(models.Model):
    store_id = models.BigAutoField(primary_key=True, default=123100000000, editable=False)
    store_no = models.CharField(max_length=50, null=True, blank=True)
    store_name = models.CharField(max_length=150, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2store', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2store', on_delete=models.DO_NOTHING)
    is_org_store = models.BooleanField(default=False)
    is_branch_store = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_general_store = models.BooleanField(default=False)
    is_main_store = models.BooleanField(default=False)
    is_sub_store = models.BooleanField(default=False)
    is_pos_report = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2store', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1231000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2store', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=112350000000, editable=False)

    def save(self, *args, **kwargs):
        store_data = store.objects.all()

        if store_data.exists() and self._state.adding:
            last_order = store_data.latest('store_id')
            user_session = store_data.latest('ss_created_session')
            modifier_session = store_data.latest('ss_modified_session')
            self.store_id = int(last_order.store_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.store_id)