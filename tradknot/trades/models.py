from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class TradeDetails(models.Model):

    BUY = 'Buy'
    SELL = 'Sell'
    TRADE_TYPE_CHOICES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]

    SOURCE_CHOICES = [
        ('CSV', 'CSV'),
        ('Manual', 'Manual'),
    ]



    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trade_datetime = models.DateTimeField()
    trade_symbol = models.CharField(max_length=10)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPE_CHOICES)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    exit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    pnl = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trade_rationale = models.TextField(null=True, blank=True)
    outcome_analysis = models.TextField(null=True, blank=True)
    emotional_state = models.TextField(null=True, blank=True)
    lessons_learned = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='Manual')



    def __str__(self):
        return f"{self.trade_datetime} - {self.trade_symbol} - {self.trade_type}"

    def calculate_pnl(self):
        if self.trade_type == 'Buy':
            return (self.exit_price - self.entry_price) * self.quantity
        elif self.trade_type == 'Sell':
            return (self.entry_price - self.exit_price) * self.quantity
        return 0

    def save(self, *args, **kwargs):
        self.pnl = self.calculate_pnl()
        super().save(*args, **kwargs)

    def clean(self):
        # Ensure trade_datetime is not set to a future date and time
        if self.trade_datetime > timezone.now():
            raise ValidationError("Trade date and time cannot be in the future.")

    class Meta:
        ordering = ['-trade_datetime']
