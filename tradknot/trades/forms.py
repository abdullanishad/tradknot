# forms.py
from django import forms
from .models import TradeDetails


class TradeDetailsForm(forms.ModelForm):
    class Meta:
        model = TradeDetails
        fields = ['trade_datetime', 'trade_symbol', 'trade_type', 'entry_price', 'exit_price', 'quantity',
                  'trade_rationale', 'outcome_analysis', 'emotional_state', 'lessons_learned', 'notes']
        # Customize widgets or add validation if needed
        widgets = {
            'trade_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            # Add other widget customizations here
        }
