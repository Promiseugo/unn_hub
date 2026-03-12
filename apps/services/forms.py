from django import forms
from .models import ServiceOffer


class ServiceOfferForm(forms.ModelForm):
    class Meta:
        model = ServiceOffer
        fields = ('title', 'description', 'price', 'price_label',
                  'category', 'delivery_mode')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
