from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile
from apps.trust.utils import validate_university_email, is_campus_email

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    matric_number = forms.CharField(
        max_length=20,
        required=False,
        label="Matric Number (optional)",
        help_text="e.g. 2019/234567. Speeds up your student verification.",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 2019/234567'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'matric_number', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        ok, error = validate_university_email(email)
        if not ok:
            raise forms.ValidationError(error)
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower().strip()
        matric = self.cleaned_data.get('matric_number', '').strip()
        if matric:
            user.matric_number = matric.upper()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Override to normalize email to lowercase before authentication.
    USERNAME_FIELD is 'email' so self.username_field is the email field.
    """
    def clean(self):
        # Lowercase the email before Django attempts authentication
        username = self.cleaned_data.get('username', '')
        if username:
            self.cleaned_data['username'] = username.lower().strip()
        return super().clean()


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'department', 'level')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class UserUpdateForm(forms.ModelForm):
    matric_number = forms.CharField(
        max_length=20,
        required=False,
        label="Matric Number",
        help_text="e.g. 2019/234567. Used for manual student verification.",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 2019/234567'}),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'matric_number')

    def clean_matric_number(self):
        val = self.cleaned_data.get('matric_number', '').strip()
        return val.upper() if val else ''
