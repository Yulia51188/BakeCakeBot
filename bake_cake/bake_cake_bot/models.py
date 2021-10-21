from django.db import models


class Client(models.Model):
    tg_chat_id = models.PositiveIntegerField('ID чата Телеграм', unique=True,
        db_index=True)
    first_name = models.CharField('Имя', max_length=100, db_index=True)

    last_name = models.CharField('Фамилия', max_length=100, db_index=True,
                                 blank=True, default='')
    phone = models.CharField('Телефон', max_length=15, db_index=True,
        blank=True, default='')
    address = models.CharField('Адрес', max_length=256, blank=True, default='')
    pd_proccessing_consent = models.BooleanField(
        'Согласие на обработку ПД', null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.tg_chat_id})'


class Category(models.Model):
    title = models.CharField('Название категории', max_length=100)
    is_mandatory = models.BooleanField('Обязательная?', default=False)
    
    def __str__(self):
        return f'{self.title}'


class Option(models.Model):
    name = models.CharField('Название', max_length=100, db_index=True)
    price = models.IntegerField('Цена', db_index=True)
    category = models.ForeignKey('Category', verbose_name='Категория',
        on_delete=models.CASCADE, db_index=True, related_name='options')

    def __str__(self):
        return f'{self.category} {self.name}'


class Cake(models.Model):
    created_by = models.ForeignKey(
        'Client',
        verbose_name='Клиент, собравший торт',
        related_name='cakes',
        on_delete=models.CASCADE
    )
    options = models.ManyToManyField(
        'Option',
        verbose_name='Параметры торта',
        related_name='used_in_cake',
        db_index=True,
    )
    text = models.CharField(
        'Надпись на торте',
        max_length=100,
        help_text='Используется только если добавлен параметр "Надпись на торте"',
        blank=True,
        default=''
    )
    is_in_order = models.BooleanField(
        'Добавлен в заказ?',
        blank=True,
        default=False
    )

    def __str__(self):
        return f'Торт {self.id} для {self.created_by}'