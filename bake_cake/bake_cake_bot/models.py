from django.db import models


class Client(models.Model):
    first_name = models.CharField('Имя', max_length=100, db_index=True)
    last_name = models.CharField('Фамилия', max_length=100, db_index=True,
                                 blank=True)
    phone = models.CharField('Телефон', max_length=15, db_index=True)
    address = models.CharField('Адрес', max_length=256, blank=True, default='')
    pd_proccessing_consent = models.NullBooleanField(
        'Согласие на обработку ПД')

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.phone})'
