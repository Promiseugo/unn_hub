from django import forms
from .models import Review

STAR_CHOICES = [
    (5, '⭐⭐⭐⭐⭐  Excellent'),
    (4, '⭐⭐⭐⭐    Good'),
    (3, '⭐⭐⭐      Average'),
    (2, '⭐⭐        Poor'),
    (1, '⭐          Terrible'),
]


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=STAR_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'star-radio'}),
        label='Your Rating',
    )

    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Share your experience (optional)...',
                'class': 'form-control',
            }),
        }
        labels = {
            'comment': 'Comment (optional)',
        }
