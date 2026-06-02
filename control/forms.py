from django import forms
from products.models import Product, Category, ProductImage
from orders.models import Order, Payment, Refund


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'short_description',
            'price', 'compare_price', 'metal_type', 'diamond_shape',
            'carat_weight', 'certification', 'stock',
            'is_featured', 'is_new_arrival', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'ctrl-input'}),
            'description': forms.Textarea(attrs={'class': 'ctrl-input', 'rows': 4}),
            'short_description': forms.TextInput(attrs={'class': 'ctrl-input'}),
            'price': forms.NumberInput(attrs={'class': 'ctrl-input'}),
            'compare_price': forms.NumberInput(attrs={'class': 'ctrl-input'}),
            'stock': forms.NumberInput(attrs={'class': 'ctrl-input'}),
            'carat_weight': forms.NumberInput(attrs={'class': 'ctrl-input'}),
            'category': forms.Select(attrs={'class': 'ctrl-select'}),
            'metal_type': forms.Select(attrs={'class': 'ctrl-select'}),
            'diamond_shape': forms.Select(attrs={'class': 'ctrl-select'}),
            'certification': forms.Select(attrs={'class': 'ctrl-select'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'parent', 'position', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'ctrl-input'}),
            'description': forms.Textarea(attrs={'class': 'ctrl-input', 'rows': 3}),
            'position': forms.NumberInput(attrs={'class': 'ctrl-input'}),
            'parent': forms.Select(attrs={'class': 'ctrl-select'}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt', 'is_primary', 'position']
        widgets = {
            'alt': forms.TextInput(attrs={'class': 'ctrl-input'}),
            'position': forms.NumberInput(attrs={'class': 'ctrl-input'}),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'ctrl-select'}),
            'notes': forms.Textarea(attrs={'class': 'ctrl-input', 'rows': 3}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method', 'status', 'amount', 'transaction_id', 'gateway', 'paid_at']
        widgets = {
            'method': forms.Select(attrs={'class': 'ctrl-select'}),
            'status': forms.Select(attrs={'class': 'ctrl-select'}),
            'amount': forms.NumberInput(attrs={'class': 'ctrl-input'}),
            'transaction_id': forms.TextInput(attrs={'class': 'ctrl-input'}),
            'gateway': forms.TextInput(attrs={'class': 'ctrl-input'}),
            'paid_at': forms.DateTimeInput(attrs={'class': 'ctrl-input', 'type': 'datetime-local'}),
        }


class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['amount', 'reason', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'ctrl-input'}),
            'reason': forms.Textarea(attrs={'class': 'ctrl-input', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'ctrl-input', 'rows': 2}),
        }


class RefundStatusForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['status', 'transaction_id', 'notes', 'processed_at']
        widgets = {
            'status': forms.Select(attrs={'class': 'ctrl-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'ctrl-input'}),
            'notes': forms.Textarea(attrs={'class': 'ctrl-input', 'rows': 2}),
            'processed_at': forms.DateTimeInput(attrs={'class': 'ctrl-input', 'type': 'datetime-local'}),
        }
