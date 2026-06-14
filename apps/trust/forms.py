from django import forms
from django.core.exceptions import ValidationError

from apps.core.validators import validate_image_size, validate_image_type
from .models import ExternalSellerApplication, Report, StudentIDVerification


class OTPVerificationForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'placeholder': 'Enter 6-digit code',
        }),
    )


class SafetyAcknowledgementForm(forms.Form):
    acknowledge = forms.BooleanField(
        label='I understand the campus safety guidelines and will use public meetup locations.',
    )


class StudentIDVerificationForm(forms.ModelForm):
    class Meta:
        model = StudentIDVerification
        fields = ('student_id_number', 'document')
        widgets = {
            'student_id_number': forms.TextInput(attrs={'placeholder': 'Optional matric/student ID number'}),
        }


class ExternalSellerApplicationForm(forms.ModelForm):
    class Meta:
        model = ExternalSellerApplication
        fields = ('business_name', 'phone_number', 'public_profile_url', 'campus_reason', 'proof_image')
        widgets = {
            'business_name': forms.TextInput(attrs={'placeholder': 'Business or trading name, if any'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone number for manual moderator review'}),
            'public_profile_url': forms.URLInput(attrs={'placeholder': 'Optional Instagram, website, LinkedIn, etc.'}),
            'campus_reason': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Explain what you sell, how you serve students, and why moderators should approve you.',
            }),
        }

    def clean_proof_image(self):
        image = self.cleaned_data.get('proof_image')
        if image:
            try:
                validate_image_size(image)
                validate_image_type(image)
            except ValidationError:
                raise
        return image


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason', 'details')
        widgets = {
            'details': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe what happened. Include dates, messages, and any warning signs.'}),
        }
