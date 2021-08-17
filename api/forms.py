from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import SubscriptionKeys


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

# checking the form used to register keys
class KeyRegisterForm(forms.Form):
    key = forms.CharField(label='Key', max_length=36)

    def clean(self):
        key = self.cleaned_data.get('key')
        try:
            key = SubscriptionKeys.objects.get(key=key)
            key.delete()
        except:
            self.add_error('key', 'The entered key is non-existent!')

