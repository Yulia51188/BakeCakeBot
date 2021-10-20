from django.contrib import admin

from .models import Client, Category, Option


class ClientAdmin(admin.ModelAdmin):
    list_display = ['tg_chat_id', 'first_name', 'last_name', 'phone',
                    'pd_proccessing_consent', 'address']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_mandatory']


class OptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    list_filter = ['category']


admin.site.register(Client, ClientAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Option, OptionAdmin)
