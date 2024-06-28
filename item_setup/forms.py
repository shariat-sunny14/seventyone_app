from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django import forms
from .models import items, item_supplierdtl

# Item setup Forms
class ItemSetupForm(forms.ModelForm):
    class Meta:
        model = items
        fields = "__all__"
    
    def clean(self):
        item_no = self.cleaned_data["item_no"]
        if items.objects.filter(item_no=item_no).exists():
            raise forms.ValidationError('Item No. Already Exists')

        item_name = self.cleaned_data["item_name"]
        if items.objects.filter(item_name=item_name).exists():
          raise forms.ValidationError('Item Name Already Exists')

# Item supplierdtl Forms
class ItemSupplierdtlForm(forms.ModelForm):
    class Meta:
        model = item_supplierdtl
        fields = "__all__"
