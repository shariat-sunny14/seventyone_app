from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django import forms
from .models import store

# Store Forms
class storeSetupForm(forms.ModelForm):
    class Meta:
        model = store
        fields = "__all__"

    def clean(self):
        store_no = self.cleaned_data["store_no"]
        if store.objects.filter(store_no=store_no).exists():
            raise forms.ValidationError('Store No. Already Exists')

        store_name = self.cleaned_data["store_name"]
        if store.objects.filter(store_name=store_name).exists():
          raise forms.ValidationError('Store Name Already Exists')
        
# Store update Forms
class storeUpdateSetupForm(forms.ModelForm):
    class Meta:
        model = store
        fields = "__all__"