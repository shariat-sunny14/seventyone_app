from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()
# User setup


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'password1', 'password2', 
        'designation', 'default_pagelink', 'expiry_date', 'expiry_status', 'phone_no', 'profile_img']

class UserUpgrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active','designation', 
                  'default_pagelink', 'expiry_date', 'expiry_status', 'phone_no', 'profile_img', 'org_id', 'branch_id']