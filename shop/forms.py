# shop/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Customer

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    shipping_address = forms.CharField(widget=forms.Textarea, required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            customer = Customer(user=user, shipping_address=self.cleaned_data['shipping_address'], phone_number=self.cleaned_data['phone_number'])
            customer.save()
        return user
