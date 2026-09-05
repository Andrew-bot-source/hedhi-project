from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import (
    CycleProfile,
    CycleRecord,
    SymptomLog,
)


class RegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
               "please choose a different username. "
                "This username is already taken."
            )
        

        return username

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email
class ProfileForm(forms.ModelForm):

    class Meta:

        model = CycleProfile

        fields = [
            "age",
            "usual_cycle_length",
            "usual_period_duration",
            "bmi",
            "irregular",
        ]

        widgets = {
            "age": forms.NumberInput(
                attrs={"min": 12, "max": 55}
            ),

            "usual_cycle_length": forms.NumberInput(
                attrs={"min": 15, "max": 60}
            ),

            "usual_period_duration": forms.NumberInput(
                attrs={"min": 2, "max": 10}
            ),

            "bmi": forms.NumberInput(
                attrs={
                    "min": 12,
                    "max": 60,
                    "step": "0.1"
                }
            ),
        }


class PeriodForm(forms.ModelForm):

    class Meta:

        model = CycleRecord

        fields = [
            "period_start",
            "period_end",
        ]

        widgets = {
            "period_start": forms.DateInput(
                attrs={"type": "date"}
            ),

            "period_end": forms.DateInput(
                attrs={"type": "date"}
            ),
        }


class SymptomForm(forms.ModelForm):

    class Meta:

        model = SymptomLog

        fields = [
            "date",
            "cramps",
            "headache",
            "flow",
            "mood",
            "stress_level",
            "sleep_hours",
            "notes",
        ]

        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"}
            ),

            "cramps": forms.NumberInput(
                attrs={"min": 0, "max": 10}
            ),

            "stress_level": forms.NumberInput(
                attrs={"min": 1, "max": 5}
            ),

            "sleep_hours": forms.NumberInput(
                attrs={
                    "min": 0,
                    "max": 24,
                    "step": "0.1"
                }
            ),
        }