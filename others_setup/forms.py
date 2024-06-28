from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django import forms
from .models import item_type, item_uom, item_category

# Item Type Forms
class ItemTypeSetupForm(forms.ModelForm):
    class Meta:
        model = item_type
        fields = "__all__"

    def clean(self):
        type_no = self.cleaned_data["type_no"]
        if item_type.objects.filter(type_no=type_no).exists():
            raise forms.ValidationError('Item Type No. Already Exists')

        type_name = self.cleaned_data["type_name"]
        if item_type.objects.filter(type_name=type_name).exists():
          raise forms.ValidationError('Item Type Name Already Exists')

# Item Type Update Forms
class ItemTypeUpdateForm(forms.ModelForm):
    class Meta:
        model = item_type
        fields = "__all__"

# Item Uom Forms
class ItemUoMSetupForm(forms.ModelForm):
    class Meta:
        model = item_uom
        fields = "__all__"

    def clean(self):
        item_uom_no = self.cleaned_data["item_uom_no"]
        if item_uom.objects.filter(item_uom_no=item_uom_no).exists():
            raise forms.ValidationError('Item UoM No. Already Exists')

        item_uom_name = self.cleaned_data["item_uom_name"]
        if item_uom.objects.filter(item_uom_name=item_uom_name).exists():
          raise forms.ValidationError('Item UoM Name Already Exists')

# Item Uom update Forms
class ItemUoMUpdateForm(forms.ModelForm):
    class Meta:
        model = item_uom
        fields = "__all__"


# Item Category Forms
class ItemCategorySetupForm(forms.ModelForm):
    class Meta:
        model = item_category
        fields = "__all__"

    def clean(self):
        category_no = self.cleaned_data["category_no"]
        if item_category.objects.filter(category_no=category_no).exists():
            raise forms.ValidationError('Item Category No. Already Exists')

        category_name = self.cleaned_data["category_name"]
        if item_category.objects.filter(category_name=category_name).exists():
          raise forms.ValidationError('Item Category Name Already Exists')
        
# Item Category Update Forms
class ItemCategoryUpdateForm(forms.ModelForm):
    class Meta:
        model = item_category
        fields = "__all__"