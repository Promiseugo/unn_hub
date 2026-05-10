from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'password1', 'password2')

    def clean_email(self):
        # Normalize to lowercase so Promise@gmail.com == promise@gmail.com
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Always store email in lowercase
        user.email = self.cleaned_data['email'].lower().strip()
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
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone')
