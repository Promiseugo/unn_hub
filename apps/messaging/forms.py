from django import forms
from .models import Message, Thread
from apps.trust.utils import contains_contact_info, redact_contact_info, scan_text_for_policy


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('body',)
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write your message...',
            }),
        }
        labels = {'body': ''}

    def clean_body(self):
        body = self.cleaned_data.get('body', '').strip()
        if scan_text_for_policy(body):
            raise forms.ValidationError("This message appears to violate marketplace safety rules.")
        return body


class NewThreadForm(forms.Form):
    """Used when contacting a seller about a listing for the first time."""
    subject = forms.CharField(max_length=255, required=False)
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Your message...'}),
        label='Message',
    )

    def clean_body(self):
        body = self.cleaned_data.get('body', '').strip()
        if scan_text_for_policy(body):
            raise forms.ValidationError("This message appears to violate marketplace safety rules.")
        return body
