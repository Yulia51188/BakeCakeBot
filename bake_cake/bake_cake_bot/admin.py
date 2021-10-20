from django.contrib import admin

from .models import Client


class ClientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'phone',
                    'pd_proccessing_consent', 'address']


admin.site.register(Client, ClientAdmin)
