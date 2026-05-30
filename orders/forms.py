from django import forms


class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-input'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-input'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-input'}))
    address_line1 = forms.CharField(max_length=250, widget=forms.TextInput(attrs={'placeholder': 'Street Address', 'class': 'form-input'}))
    address_line2 = forms.CharField(max_length=250, required=False, widget=forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc. (optional)', 'class': 'form-input'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-input'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'State / Province', 'class': 'form-input'}))
    country = forms.CharField(max_length=100, initial='India', widget=forms.TextInput(attrs={'placeholder': 'Country', 'class': 'form-input'}))
    pincode = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'PIN / Postal Code', 'class': 'form-input'}))
