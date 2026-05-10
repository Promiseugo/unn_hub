from django import forms
from django.core.exceptions import ValidationError
from .models import RentalListing, RentalInquiry
from apps.core.validators import validate_positive_price, validate_image_size, validate_image_type, validate_video_size, validate_video_type


class RentalListingForm(forms.ModelForm):
    # Amenities rendered as checkboxes
    amenities = forms.MultipleChoiceField(
        choices=RentalListing.AMENITY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Amenities Available",
    )

    class Meta:
        model = RentalListing
        fields = (
            'listing_type', 'title', 'description', 'rental_type', 'price', 'rental_period',
            'subsequent_payment', 'subsequent_payment_note',
            'address', 'area', 'gender_preference', 'available_from',
            'rooms_available', 'amenities',
        )
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Clean Self-contain at Hilltop',
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the property — size, furnishing, neighbours, proximity to campus...',
            }),
            'address': forms.TextInput(attrs={
                'placeholder': 'e.g. No. 5 Odim Road, Nsukka',
            }),
            'area': forms.TextInput(attrs={
                'placeholder': 'e.g. Odim, Hilltop, University Road',
            }),
            'price': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'min': '1',
            }),
            'available_from': forms.DateInput(attrs={
                'type': 'date',
            }),
            'rooms_available': forms.NumberInput(attrs={
                'min': '1',
                'max': '20',
            }),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None:
            validate_positive_price(price)
        return price

    def clean_amenities(self):
        """Convert list of selected amenities to comma-separated string for storage."""
        amenities = self.cleaned_data.get('amenities', [])
        return ','.join(amenities)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing, convert stored comma string back to list for checkboxes
        if self.instance and self.instance.amenities:
            self.initial['amenities'] = self.instance.get_amenities_list()


class RentalInquiryForm(forms.ModelForm):
    class Meta:
        model = RentalInquiry
        fields = ('message',)
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Introduce yourself — your level, department, move-in date, any questions...',
            }),
        }
        labels = {
            'message': 'Your Message to the Landlord',
        }


class MultiImageValidator:
    @staticmethod
    def validate(files):
        errors = []
        if len(files) > 5:
            errors.append("You can upload a maximum of 5 images.")
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
        if not file:
            return None
        try:
            validate_video_size(file)
            validate_video_type(file)
        except ValidationError as e:
            return e.message
        return None
