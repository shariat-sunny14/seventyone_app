from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.
class module_list(models.Model):
    module_id = models.BigAutoField(
        primary_key=True, default=10000000001, editable=False)
    module_no = models.CharField(max_length=50, null=True, blank=True)
    module_name = models.CharField(max_length=150, null=True, blank=True)
    module_code = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2module_list', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1200000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2module_list', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=110000000000, editable=False)

    def save(self, *args, **kwargs):
        module_list_data = module_list.objects.all()

        if module_list_data.exists() and self._state.adding:
            last_order = module_list_data.latest('module_id')
            user_session = module_list_data.latest('ss_created_session')
            modifier_session = module_list_data.latest('ss_modified_session')
            self.module_id = int(last_order.module_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.module_id)

# module type


class module_type(models.Model):
    type_id = models.BigAutoField(
        primary_key=True, default=10100000001, editable=False)
    type_no = models.CharField(max_length=50, null=True, blank=True)
    type_name = models.CharField(max_length=150, null=True, blank=True)
    type_code = models.CharField(max_length=50, null=True, blank=True)
    module_id = models.ForeignKey(module_list, null=True, blank=True,
                                  related_name='module_id2moduletype', on_delete=models.DO_NOTHING, editable=False)
    type_icon = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2module_type', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1201000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2module_type', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=110100000000, editable=False)

    def save(self, *args, **kwargs):
        module_type_data = module_type.objects.all()

        if module_type_data.exists() and self._state.adding:
            last_order = module_type_data.latest('type_id')
            user_session = module_type_data.latest('ss_created_session')
            modifier_session = module_type_data.latest('ss_modified_session')
            self.type_id = int(last_order.type_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.type_id)


# module feature
class feature_list(models.Model):
    feature_id = models.BigAutoField(
        primary_key=True, default=11100000001, editable=False)
    feature_no = models.CharField(max_length=50, null=True, blank=True)
    feature_name = models.CharField(max_length=150, null=True, blank=True)
    feature_type = models.CharField(max_length=10, null=True, blank=True)
    serial_no = models.BigIntegerField(null=True, blank=True)
    feature_code = models.CharField(max_length=50, null=True, blank=True)
    feature_page_link = models.CharField(max_length=100, null=True, blank=True)
    module_id = models.ForeignKey(module_list, null=True, blank=True,
                                  related_name='module_id2feature_list', on_delete=models.DO_NOTHING, editable=False)
    type_id = models.ForeignKey(module_type, null=True, blank=True,
                                related_name='type_id2feature_list', on_delete=models.DO_NOTHING, editable=False)
    feature_icon = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2feature_list', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1111000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2feature_list', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=111200000000, editable=False)

    def save(self, *args, **kwargs):
        feature_list_data = feature_list.objects.all()

        if feature_list_data.exists() and self._state.adding:
            last_order = feature_list_data.latest('feature_id')
            user_session = feature_list_data.latest('ss_created_session')
            modifier_session = feature_list_data.latest('ss_modified_session')
            self.feature_id = int(last_order.feature_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.feature_id)
