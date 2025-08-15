from django.contrib import admin
from .models import Item, Tax, Order, Discount
# Register your models here.

admin.site.register(Item)
admin.site.register(Tax)
admin.site.register(Order)
admin.site.register(Discount)