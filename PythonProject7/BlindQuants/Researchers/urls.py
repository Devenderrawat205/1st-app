# Researchers/urls.py
from django.urls import path
from . import views

app_name = 'researchers' # Defines the namespace for this app

urlpatterns = [
    path('', views.stock_list, name='stock_list'), # This now serves as the root (e.g., /)
    path('chart/<str:stock_symbol>/', views.stock_chart_view, name='stock_chart'),
    path('backtest/', views.run_backtest_view, name='backtest'),
    path('update-indicator/', views.update_indicator, name='update_indicator'),
    path('save-drawing/', views.save_drawing, name='save_drawing'),
    path('download-excel/', views.download_backtest_excel, name='download_excel'),
]