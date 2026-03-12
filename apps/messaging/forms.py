from django import forms
from .models import Message, Thread


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


class NewThreadForm(forms.Form):
    """Used when contacting a seller about a listing for the first time."""
    subject = forms.CharField(max_length=255, required=False)
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Your message...'}),
        label='Message',
    )
