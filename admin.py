from django.contrib import admin
from ypl.models import Exchange, Product


class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'parent')
    list_filter = ['parent']


class ProductAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company', 'market_cap')
    filter_horizontal = ['exchanges']


admin.site.register(Exchange, ExchangeAdmin)

admin.site.register(Product, ProductAdmin)