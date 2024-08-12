from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import TradeDetails
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, DecimalField, Case, When, Count, F, Value, IntegerField, Q


class TradeCreateView(LoginRequiredMixin, CreateView):
    model = TradeDetails
    template_name = 'trades/addtrade.html'
    fields = ['trade_datetime', 'trade_symbol', 'trade_type', 'entry_price', 'exit_price', 'quantity',
              'trade_rationale', 'outcome_analysis', 'emotional_state', 'lessons_learned', 'notes']
    success_url = reverse_lazy('tradebook')

    def form_valid(self, form):
        form.instance.user = self.request.user
        print("Form is valid. Data:", form.cleaned_data)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form is invalid. Errors:", form.errors)
        return super().form_invalid(form)


class TradeListView(LoginRequiredMixin, ListView):
    model = TradeDetails
    template_name = 'trades/tradebook.html'
    context_object_name = 'trades'

    def get_queryset(self):
        # Filter trades by the logged-in user
        return TradeDetails.objects.filter(user=self.request.user)


# class TradeDetailView(DetailView):
#     model = TradeDetails
#     template_name = 'trades/trade_detail.html'
#     context_object_name = 'trade'




# class TradeUpdateView(UpdateView):
#     model = TradeDetails
#     template_name = 'trades/addtrade.html'
#     fields = ['user', 'trade_datetime', 'trade_symbol', 'trade_type', 'entry_price', 'exit_price', 'quantity',
#               'trade_rationale', 'outcome_analysis', 'emotional_state', 'lessons_learned', 'notes']
#     success_url = reverse_lazy('tradebook')

# class TradeDeleteView(DeleteView):
#     model = TradeDetails
#     template_name = 'trades/trade_confirm_delete.html'
#     success_url = reverse_lazy('tradebook')

def home(request):
    return render(request, 'trades/home.html')


# @login_required
# def performance(request):
#     # Annotate each row with the calculation (entry_price + exit_price) * quantity
#     annotated_queryset = TradeDetails.objects.filter(user=request.user).annotate(
#         calculated_value=Case(
#             When(trade_type='Sell', then=(F('entry_price') - F('exit_price'))),
#             When(trade_type='Buy', then=(F('exit_price') - F('entry_price'))),
#             output_field=DecimalField()
#         ),
#         total_value=F('calculated_value') * F('quantity')
#     )
#
#     # Aggregate the total of the annotated field
#     total_sum = annotated_queryset.aggregate(total_sum=Sum('total_value'))
#
#     return render(request, 'trades/performance.html', {'total_sum': total_sum['total_sum'] or 0})

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
    # Sort trades by date or order if applicable
    sorted_trades = trades.order_by('trade_datetime')  # Adjust field name as needed

    max_drawdown = 0
    peak = float('-inf')
    trough = float('inf')

    # Calculate cumulative returns
    for trade in sorted_trades:
        current_value = trade.entry_price * trade.quantity  # Adjust as needed
        if current_value > peak:
            peak = current_value
            trough = current_value
        else:
            if current_value < trough:
                trough = current_value
            drawdown = (peak - trough) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    max_drawdown_percentage = max_drawdown * 100

    return render(request, 'trades/performance.html', {
        'total_sum': total_sum['total_sum'] or 0,
        'win_count': win_count,
        'loss_count': loss_count,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown_percentage
    })
