from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import TradeDetails
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, DecimalField, Case, When, Count, F, Value, IntegerField, Q
from django.contrib import messages
from .forms import TradeDetailsForm  # Ensure you have a form defined for TradeDetails
from django.views.generic.edit import View


# trade create view class
class TradeCreateView(LoginRequiredMixin, CreateView):
    model = TradeDetails
    form_class = TradeDetailsForm
    template_name = 'trades/addtrade.html'
    success_url = reverse_lazy('tradebook')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Trade successfully created!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


# trade list view class
class TradeListView(LoginRequiredMixin, ListView):
    model = TradeDetails
    template_name = 'trades/tradebook.html'
    context_object_name = 'trades'

    def get_queryset(self):
        # Filter trades by the logged-in user
        return TradeDetails.objects.filter(user=self.request.user)


# trade update view class
class TradeUpdateView(LoginRequiredMixin, UpdateView):
    model = TradeDetails
    form_class = TradeDetailsForm
    template_name = 'trades/update_trade.html'
    success_url = reverse_lazy('tradebook')  # Redirect to trade list view after update

    def get_queryset(self):
        # Ensure that users can only update their own trades
        return TradeDetails.objects.filter(user=self.request.user)

    def form_valid(self, form):
        # Optionally, perform additional actions before saving the form
        return super().form_valid(form)


# trade delete view class
class TradeDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        trade_id = request.POST.get('trade_id')  # Get trade ID from POST data
        trade = get_object_or_404(TradeDetails, id=trade_id, user=request.user)
        trade.delete()
        return redirect('tradebook')


# homepage function
def home(request):
    return render(request, 'trades/home.html')


# function to calculate portfolio values
def calculate_portfolio_values():
    trades = TradeDetails.objects.all().order_by('trade_datetime')
    portfolio_values = []
    cumulative_pnl = 0
    for trade in trades:
        cumulative_pnl += trade.pnl
        portfolio_values.append(cumulative_pnl)
    return portfolio_values


# function to calculate maximum drawdown
def calculate_maximum_drawdown(portfolio_values):
    max_drawdown = 0
    if not portfolio_values:
        return None
    peak_value = portfolio_values[0]

    for value in portfolio_values:
        if value > peak_value:
            peak_value = value
        drawdown = peak_value - value
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


# function to calculate maximum drawdown percentage
def calculate_maximum_drawdown_percentage(max_drawdown, peak_value):
    if peak_value == 0:
        return 0
    return (max_drawdown / peak_value) * 100


# function to track performance of trades
@login_required
def performance(request):
    # Annotate each row with the calculation (entry_price + exit_price) * quantity
    annotated_queryset = TradeDetails.objects.filter(user=request.user).annotate(
        calculated_value=Case(
            When(trade_type='Sell', then=(F('entry_price') - F('exit_price'))),
            When(trade_type='Buy', then=(F('exit_price') - F('entry_price'))),
            output_field=DecimalField()
        ),
        total_value=F('calculated_value') * F('quantity')
    )

    # Aggregate the total of the annotated field
    total_sum = annotated_queryset.aggregate(total_sum=Sum('total_value'))

    # Annotate each trade with whether it's a win or loss
    trades = TradeDetails.objects.filter(user=request.user)
    annotated_trades = trades.annotate(
        result=Case(
            When(trade_type='Buy', then=Case(
                When(exit_price__gt=F('entry_price'), then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )),
            When(trade_type='Sell', then=Case(
                When(exit_price__lt=F('entry_price'), then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )),
            default=Value(0),
            output_field=IntegerField()
        )
    )

    # Count wins and losses
    win_count = annotated_trades.aggregate(win_count=Count('id', filter=Q(result=1)))['win_count']
    loss_count = annotated_trades.aggregate(loss_count=Count('id', filter=Q(result=0)))['loss_count']
    total_count = annotated_trades.count()

    # Calculate Win/Loss Ratio
    win_count = win_count or 0
    loss_count = loss_count or 0
    win_rate = (win_count / total_count * 100) if total_count > 0 else 0  # Handle division by zero

    # Calculate Maximum Drawdown
    portfolio_values = calculate_portfolio_values()
    if portfolio_values:
        max_drawdown = calculate_maximum_drawdown(portfolio_values)
        peak_value = max(portfolio_values)
        max_drawdown_percentage = calculate_maximum_drawdown_percentage(max_drawdown, peak_value)
    else:
        max_drawdown = 0
        max_drawdown_percentage = 0

    return render(request, 'trades/performance.html', {
        'total_sum': total_sum['total_sum'] or 0,
        'win_count': win_count,
        'loss_count': loss_count,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'max_dd_percentage': max_drawdown_percentage
    })

