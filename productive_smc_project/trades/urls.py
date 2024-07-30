from django.urls import path
from .views import TradeCreateView, TradeListView, home

urlpatterns = [
    path('addtrade/', TradeCreateView.as_view(), name='addtrade'),
    path('tradebook/', TradeListView.as_view(), name='tradebook'),
    path('',home,name='home'),
    # other paths...
]

