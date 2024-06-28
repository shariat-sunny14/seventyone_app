
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django import forms
from .models import opening_stock, opening_stockdtl

# Opening stock Forms
class OpeningStockForm(forms.ModelForm):
    class Meta:
        model = opening_stock
        fields = "__all__"
        

# Opening stock dtl Forms
class OpeningStockdtlForm(forms.ModelForm):
    class Meta:
        model = opening_stockdtl
        fields = "__all__"
    
    def clean(self):
        item_name = self.cleaned_data["item_name"]
        if opening_stockdtl.objects.filter(item_name=item_name).exists():
            raise forms.ValidationError('Item Name Already Exists')