# yourapp/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

class RegistrationForm(UserCreationForm):
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )
    password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
    )

    # Additional fields for UserProfile
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    user_type = forms.ChoiceField(
        choices=UserProfile.USERTYPE_CHOICE,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'user_type'})
    )
    roll_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roll Number..', 'id': 'roll_number_field'})
    )
    staff_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff ID', 'id': 'staff_id_field'})
    )
    department = forms.ChoiceField(
        choices=UserProfile.DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=UserProfile.GENDER_CHOICE,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    batch = forms.ChoiceField(
        choices=UserProfile.BATCH_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'batch_field'})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'name', 'user_type',
                  'roll_number', 'staff_id', 'department', 'gender', 'batch',
                  'phone_number', 'photo')

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        roll_number = cleaned_data.get('roll_number')
        staff_id = cleaned_data.get('staff_id')
        batch = cleaned_data.get('batch')

        if user_type == 'STUDENT':
            if not roll_number:
                self.add_error('roll_number', 'Roll number is required for students')
            if not batch:
                self.add_error('batch', 'Batch is required for students')
        elif user_type == 'FACULTY':
            if not staff_id:
                self.add_error('staff_id', 'Staff ID is required for faculty')

        return cleaned_data