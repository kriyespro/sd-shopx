from django import forms

from .models import UserProfile


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'phone',
            'address_line1',
            'city',
            'state',
            'country',
            'pincode',
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-navy-500',
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-navy-500',
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-navy-500',
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-navy-500',
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-navy-500',
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-navy-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.user = user
        name_attrs = {
            'class': 'w-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-navy-500',
        }
        self.fields['first_name'].widget.attrs.update(name_attrs)
        self.fields['last_name'].widget.attrs.update(name_attrs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                self.user.save(update_fields=['first_name', 'last_name'])
        if commit:
            profile.save()
        return profile
