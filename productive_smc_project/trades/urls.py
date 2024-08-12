from django.urls import path
from .views import TradeCreateView, TradeListView, home, performance

urlpatterns = [
    path('addtrade/', TradeCreateView.as_view(), name='addtrade'),
    path('tradebook/', TradeListView.as_view(), name='tradebook'),
    path('performance/', performance, name='performance'),
    path('',home,name='home'),
    # other paths...
]

