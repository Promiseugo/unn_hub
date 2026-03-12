from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Profile


class RegisterForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm to add email
    as required and include first/last name fields.
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class LoginForm(AuthenticationForm):
    """
    Uses Django's built-in auth form — no changes needed.
    Kept here for a consistent import pattern.
    """
    pass


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'department', 'level')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone')
