from django.urls import path
from .views import item_view, buy_view, buy_order_view, order_view

urlpatterns = [
    path("item/<int:item_id>/", item_view, name="item_view"),
    path("buy/<int:item_id>/", buy_view, name="buy_view"),
    path("order/<int:order_id>/", order_view, name="order_view"),
    path("buy_order/<int:order_id>/", buy_order_view, name="buy_order_view"),
]
