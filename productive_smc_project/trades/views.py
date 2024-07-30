from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import TradeDetails
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect


class TradeListView(ListView):
    model = TradeDetails
    template_name = 'trades/tradebook.html'
    context_object_name = 'trades'


# class TradeDetailView(DetailView):
#     model = TradeDetails
#     template_name = 'trades/trade_detail.html'
#     context_object_name = 'trade'


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


class TradeUpdateView(UpdateView):
    model = TradeDetails
    template_name = 'trades/addtrade.html'
    fields = ['user', 'trade_datetime', 'trade_symbol', 'trade_type', 'entry_price', 'exit_price', 'quantity',
              'trade_rationale', 'outcome_analysis', 'emotional_state', 'lessons_learned', 'notes']
    success_url = reverse_lazy('tradebook')

# class TradeDeleteView(DeleteView):
#     model = TradeDetails
#     template_name = 'trades/trade_confirm_delete.html'
#     success_url = reverse_lazy('tradebook')

def home(request):
    return render(request, 'trades/home.html')