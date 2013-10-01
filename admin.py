from django.contrib import admin
from corpdb.models import Exchange, Product


class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'parent')
    list_filter = ['parent']


class ProductAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company', 'market_cap', 'ex', 'subex')
    list_filter = ['exchanges']
    filter_horizontal = ['exchanges']


admin.site.register(Exchange, ExchangeAdmin)

admin.site.register(Product, ProductAdmin)
