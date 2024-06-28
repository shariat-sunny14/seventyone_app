from django.db import models
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