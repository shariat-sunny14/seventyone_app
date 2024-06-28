from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django import forms
from .models import suppliers, manufacturer

# Suppliers Forms
class SuppliersSetupForm(forms.ModelForm):
    class Meta:
        model = suppliers
        fields = "__all__"

    def clean(self):
        supplier_no = self.cleaned_data["supplier_no"]
        if suppliers.objects.filter(supplier_no=supplier_no).exists():
            raise forms.ValidationError('Supplier No Already Exists')

        supplier_name = self.cleaned_data["supplier_name"]
        if suppliers.objects.filter(supplier_name=supplier_name).exists():
          raise forms.ValidationError('Supplier Name Already Exists')

# Suppliers Update Forms
class SuppliersUpdateForm(forms.ModelForm):
    class Meta:
        model = suppliers
        fields = "__all__"


# Manufacturer Forms
class ManufacturerSetupForm(forms.ModelForm):
    class Meta:
        model = manufacturer
        fields = "__all__"

    def clean(self):
        manufac_no = self.cleaned_data["manufac_no"]
        if manufacturer.objects.filter(manufac_no=manufac_no).exists():
            raise forms.ValidationError('Manufacturer No Already Exists')

        manufac_name = self.cleaned_data["manufac_name"]
        if manufacturer.objects.filter(manufac_name=manufac_name).exists():
          raise forms.ValidationError('Manufacturer Name Already Exists')
        

# Manufacturer Update Forms
class ManufacturerUpdateForm(forms.ModelForm):
    class Meta:
        model = manufacturer
        fields = "__all__"