from django import forms
from .models import Listing, ListingImage


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ('title', 'description', 'price', 'category', 'condition', 'location')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ('image', 'is_primary')
