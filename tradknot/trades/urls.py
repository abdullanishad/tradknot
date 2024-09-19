from django.urls import path
from .views import TradeCreateView, TradeListView, TradeDetailView, TradeUpdateView, TradeDeleteView, home, performance

urlpatterns = [
    path('addtrade/', TradeCreateView.as_view(), name='addtrade'),
    path('tradebook/', TradeListView.as_view(), name='tradebook'),
    path('trade/<int:pk>/', TradeDetailView.as_view(), name='trade_detail'),
    path('trades/update/<int:pk>/', TradeUpdateView.as_view(), name='update_trade'),
    path('trade/<int:pk>/delete/', TradeDeleteView.as_view(), name='trade-delete'),
    path('performance/', performance, name='performance'),
    path('',home,name='home'),
    # other paths...
]

