from django import forms
from django.utils import timezone
from inventory.models import Maintenance, Item

class MaintenanceForm(forms.ModelForm):
    # Form for scheduling maintenance
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_available=True),
        required=True,
        empty_label="Choose an item...",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Maintenance
        fields = ['item', 'maintenance_date', 'description']
        widgets = {
            'maintenance_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
            )
        }

    def clean_maintenance_date(self):
        # Validate maintenance date
        date = self.cleaned_data['maintenance_date']
        if date and date < timezone.now():
            raise forms.ValidationError("Maintenance date cannot be in the past")
        return date

class ReservationForm(forms.Form):
    # Form for creating reservations
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    def clean(self):
        # Validate reservation dates
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date < timezone.now():
                raise forms.ValidationError("Start date cannot be in the past")
            if end_date <= start_date:
                raise forms.ValidationError("End date must be after start date") 