from django import forms
from django.core.exceptions import ValidationError
from .models import ServiceOffer
from apps.core.validators import validate_positive_price, validate_video_size, validate_video_type
from apps.trust.utils import scan_text_for_policy


class ServiceOfferForm(forms.ModelForm):
    class Meta:
        model = ServiceOffer
        fields = ('title', 'description', 'price', 'price_label', 'category', 'delivery_mode')
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe what you offer, your experience, availability...',
            }),
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Python Tutoring for 200L students'}),
            'price': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '1'}),
            'price_label': forms.TextInput(attrs={'placeholder': 'e.g. per hour, per session, negotiable'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None:
            validate_positive_price(price)
        return price

    def clean(self):
        cleaned = super().clean()
        title = cleaned.get('title', '')
        description = cleaned.get('description', '')
        if scan_text_for_policy(f'{title} {description}'):
            raise ValidationError(
                "This service appears to include prohibited or unsafe content. "
                "Please review the marketplace rules before posting."
            )
        return cleaned


class VideoValidator:
    @staticmethod
    def validate(file):
        if not file:
            return None
        try:
            validate_video_size(file)
            validate_video_type(file)
        except ValidationError as e:
            return e.message
        return None
