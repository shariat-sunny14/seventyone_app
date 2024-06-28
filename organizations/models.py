from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


# organizations list models here.
class organizationlst(models.Model):
    org_id = models.BigAutoField(primary_key=True, default=101110000000, editable=False)
    org_no = models.CharField(max_length=50, null=True, blank=True)
    org_name = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)
    division = models.CharField(max_length=200, null=True, blank=True)
    district = models.CharField(max_length=200, null=True, blank=True)
    upazila = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=200, null=True, blank=True)
    website = models.CharField(max_length=200, null=True, blank=True)
    hotline = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    org_logo = models.ImageField(upload_to='org_logos', max_length=255, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2org', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1300000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2org', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=140000000000, editable=False)

    def save(self, *args, **kwargs):
        org_data = organizationlst.objects.all()

        if org_data.exists() and self._state.adding:
            last_order = org_data.latest('org_id')
            user_session = org_data.latest('ss_created_session')
            modifier_session = org_data.latest('ss_modified_session')
            self.org_id = int(last_order.org_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.org_id)
    


# branchs list models here.
class branchslist(models.Model):
    branch_id = models.BigAutoField(primary_key=True, default=100100000000, editable=False)
    branch_no = models.CharField(max_length=50, null=True, blank=True)
    branch_name = models.CharField(max_length=200, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2branchslist', on_delete=models.DO_NOTHING)
    country = models.CharField(max_length=200, null=True, blank=True)
    division = models.CharField(max_length=200, null=True, blank=True)
    district = models.CharField(max_length=200, null=True, blank=True)
    upazila = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=200, null=True, blank=True)
    website = models.CharField(max_length=200, null=True, blank=True)
    hotline = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    branch_logo = models.ImageField(upload_to='branch_logos', max_length=255, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2branchs', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1340000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2branchs', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=145000000000, editable=False)

    def save(self, *args, **kwargs):
        branch_data = branchslist.objects.all()

        if branch_data.exists() and self._state.adding:
            last_order = branch_data.latest('branch_id')
            user_session = branch_data.latest('ss_created_session')
            modifier_session = branch_data.latest('ss_modified_session')
            self.branch_id = int(last_order.branch_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.branch_id)