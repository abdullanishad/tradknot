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
import csv
from django.urls import reverse
from django.utils.dateparse import parse_datetime


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


class TradeDetailView(DetailView):
    model = TradeDetails
    template_name = 'trades/trade_detail.html'
    context_object_name = 'trade'


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


import pandas as pd
from decimal import Decimal

def upload_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')

        if not csv_file.name.endswith('.csv'):
            return HttpResponse('File is not CSV format', status=400)

        df = pd.read_csv(csv_file)

        # Initialize list to store results
        results = []

        engaged_symbol = []

        for index, row_x in df.iterrows():
            if row_x['symbol'] in engaged_symbol:
                continue

            df_filt = df[df.symbol == row_x['symbol']]

            unrealised_value = 0
            unrealised_qty = 0
            total_buy_value = 0
            total_sell_value = 0
            tot_buy_qty = 0
            tot_sell_qty = 0

            for _, row in df_filt.iterrows():
                if row.trade_type == 'buy':
                    tot_buy_qty += row.quantity
                    unrealised_qty += row.quantity
                    total_buy_value += row.quantity * row.price
                    unrealised_value += row.quantity * row.price
                else:
                    tot_sell_qty += row.quantity
                    unrealised_qty -= row.quantity
                    total_sell_value += row.quantity * row.price
                    unrealised_value -= row.quantity * row.price

            # Skip processing if there's no buy or sell
            if tot_buy_qty == 0 or tot_sell_qty == 0:
                continue

            realised_qty = max((tot_buy_qty + tot_sell_qty - abs(unrealised_qty)) / 2, 1)

            buy_avg = round(total_buy_value / tot_buy_qty, 2)
            sell_avg = round(total_sell_value / realised_qty, 2) if unrealised_qty <= 0 else round(
                total_sell_value / tot_sell_qty, 2)

            realised_pnl = (sell_avg - buy_avg) * realised_qty

            # Append results to the list
            results.append({
                'order_execution_time': row_x.order_execution_time,
                'symbol': row_x.symbol,
                'type': row_x.trade_type,
                'buy_avg': buy_avg,
                'sell_avg': sell_avg,
                'qty': realised_qty,
                'realised_pnl': realised_pnl
            })

            engaged_symbol.append(row_x['symbol'])

        # Create DataFrame from results
        df_results = pd.DataFrame(results)


        # decoded_file = df_results.read().decode('utf-8').splitlines()
        # csv_reader = csv.reader(decoded_file)
        #
        # next(csv_reader)  # Skip the title row

        for index, row in df_results.iterrows():
            try:
                # Extract necessary fields from CSV
                trade_datetime = parse_datetime(row[0])
                trade_symbol = row[1]
                trade_type = row[2].capitalize()  # 'Buy' or 'Sell'
                entry_price = Decimal(row[3])     # Convert to Decimal
                exit_price = Decimal(row[4])     # Convert to Decimal
                quantity = int(float(row[5]))

                trade = TradeDetails(
                    user=request.user,
                    trade_datetime=trade_datetime,
                    trade_symbol=trade_symbol,
                    trade_type=trade_type,
                    entry_price=entry_price,
                    exit_price=exit_price,  # Exit price as Decimal
                    quantity=quantity,
                    source='CSV'
                )
                trade.save()


            except Exception as e:
                print(f"Error processing row: {row}, error: {e}")
                continue

        return redirect(reverse('tradebook'))

    return redirect(reverse('addtrade'))



def list_trades(request):
    # Fetch trades based on source
    manual_trades = TradeDetails.objects.filter(user=request.user, source='Manual')
    csv_trades = TradeDetails.objects.filter(user=request.user, source='CSV')

    return render(request, 'trade_list.html', {
        'manual_trades': manual_trades,
        'csv_trades': csv_trades,
    })

