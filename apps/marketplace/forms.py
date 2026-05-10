from django import forms
from django.core.exceptions import ValidationError
from .models import Listing
from apps.core.validators import (
    validate_positive_price, validate_image_size,
    validate_image_type, validate_video_size, validate_video_type
)


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ('title', 'description', 'price', 'category', 'condition', 'location')
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the item — condition, age, reason for selling...',
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g. Odim Hostel, Faculty of Engineering',
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. HP EliteBook 840 — 8GB RAM, 256GB SSD',
            }),
            'price': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '1'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None:
            validate_positive_price(price)
        return price


class MultiImageValidator:
    @staticmethod
    def validate(files):
        errors = []
        if len(files) > 5:
            errors.append("You can upload a maximum of 5 images.")
            return errors
        for f in files:
            try:
                validate_image_size(f)
                validate_image_type(f)
            except ValidationError as e:
                errors.append(f"{f.name}: {e.message}")
        return errors


class VideoValidator:
    @staticmethod
    def validate(file):
        """Returns error string or None if valid."""
        if not file:
            return None
        try:
            validate_video_size(file)
            validate_video_type(file)
        except ValidationError as e:
            return e.message
        return None
