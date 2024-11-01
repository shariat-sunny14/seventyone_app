from django.db import models
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    user_id = models.BigAutoField(primary_key=True, default=123401000000, editable=False)
    username = models.CharField(max_length=200, unique=True)
    org_id = models.BigIntegerField(null=True, blank=True)
    branch_id = models.BigIntegerField(null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    default_pagelink = models.CharField(max_length=100, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    expiry_status = models.BooleanField(default=False)
    password = models.CharField(max_length=100)
    is_login_status = models.BooleanField(default=False)
    ss_creator = models.ForeignKey('self', null=True, blank=True, related_name='ss_creator2user', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1010100000000, editable=False)
    ss_modifier = models.ForeignKey('self', null=True, blank=True, related_name='ss_modifier2user', on_delete=models.DO_NOTHING, editable=False)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1110100000000, editable=False)
    phone_no = models.BigIntegerField(null=True, blank=True, unique=True)
    profile_img = models.ImageField(upload_to='user_profile', max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        user_data = User.objects.all()

        if user_data.exists() and self._state.adding:
            last_order = user_data.latest('user_id')
            user_session = user_data.latest('ss_created_session')
            modifier_session = user_data.latest('ss_modified_session')
            self.user_id = int(last_order.user_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.user_id)
    

# system shut down
class SystemShutdown(models.Model):
    sys_id = models.BigAutoField(primary_key=True)
    sys_shut_down_date = models.DateField(default=timezone.now, editable=False)
    sys_down_time_validity = models.DateTimeField()
    is_sys_shut_down = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2sys_shutd', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2sys_shutd', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if self._state.adding:  # Only modify IDs if it's a new record
            # Fetch the latest record for incrementing IDs and sessions
            last_record = SystemShutdown.objects.order_by('-sys_id').first()

            if last_record:
                self.sys_id = last_record.sys_id + 1
                self.ss_created_session = (last_record.ss_created_session or 2234567000000) + 1
                self.ss_modified_session = (last_record.ss_modified_session or 1234673500000) + 1
            else:
                # Initialize with default values if no previous record exists
                self.sys_id = 334455560000
                self.ss_created_session = 2234567000000
                self.ss_modified_session = 1234673500000

        super().save(*args, **kwargs)

    def __str__(self):
        return f"System Shutdown ID: {self.sys_id}"