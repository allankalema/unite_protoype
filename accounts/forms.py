from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class TeacherRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=255)
    email = forms.EmailField()
    institution_name = forms.CharField(max_length=255, required=False)
    district = forms.CharField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "full_name",
            "email",
            "institution_name",
            "district",
            "phone_number",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            profile = user.profile
            profile.full_name = self.cleaned_data["full_name"]
            profile.email = self.cleaned_data["email"]
            profile.institution_name = self.cleaned_data.get("institution_name", "")
            profile.district = self.cleaned_data.get("district", "")
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.role = Profile.ROLE_TEACHER
            profile.save()

        return user


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "email", "institution_name", "district", "phone_number"]
