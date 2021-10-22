from django.db import models
from django.db.models import Sum


class Client(models.Model):
    tg_chat_id = models.PositiveIntegerField(
        'ID чата Телеграм',
        unique=True,
        db_index=True
    )
    first_name = models.CharField('Имя', max_length=100, db_index=True)

    last_name = models.CharField(
        'Фамилия',
        max_length=100,
        db_index=True,
        blank=True,
        default=''
    )
    phone = models.CharField(
        'Телефон',
        max_length=15,
        db_index=True,
        blank=True,
        default=''
    )
    address = models.CharField('Адрес', max_length=256, blank=True, default='')
    pd_proccessing_consent = models.BooleanField(
        'Согласие на обработку ПД',
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.tg_chat_id})'


class Category(models.Model):
    title = models.CharField('Название категории', max_length=100)
    is_mandatory = models.BooleanField('Обязательная?', default=False)

    choice_order = models.IntegerField(
        'Порядок выбора опций категории',
        default=100000,
    )
    
    def __str__(self):
        return f'{self.title}'


class Option(models.Model):
    name = models.CharField('Название', max_length=100, db_index=True)
    price = models.IntegerField('Цена', db_index=True)
    category = models.ForeignKey(
        'Category',
        verbose_name='Категория',
        on_delete=models.CASCADE,
        db_index=True,
        related_name='options'
    )

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
    price = models.IntegerField('Цена торта', default=0)

    def save(self, *args, **kwargs):
        if self.id and self.options.all():
            self.price = (
                self.options
                .aggregate(total_price=Sum('price'))['total_price']
            )
        super(Cake, self).save(*args, **kwargs)

    def __str__(self):
        return f'Торт для {self.created_by}, цена {self.price}'


class Order(models.Model):
    ORDER_STATES = [
        (0, 'Заявка формируется'),
        (1, 'Заявка обрабатывается'), 
        (2, 'Торт готовится'), 
        (3, 'Торт в пути'), 
        (4, 'Завершен'), 
    ]
    status = models.IntegerField(
        'Статус заказа',
        choices=ORDER_STATES,
        default=0
    )

    client = models.ForeignKey(
        'Client',
        verbose_name='Клиент',
        related_name='orders',
        on_delete=models.CASCADE,      
    )

    total_amount = models.IntegerField('Сумма заказа', default=0) 
    
    cakes = models.ManyToManyField(
        'Cake',
        verbose_name='Торты в заказе',
        related_name='in_orders',
    )
    created_at = models.DateTimeField(
        'Дата создания заказа',
        auto_now_add=True
    )
    modified_at = models.DateTimeField(
        'Дата изменения заказа',
        auto_now=True
    )

    def save(self, *args, **kwargs):
        # Стоимость заказа пересчитывается только в случае,
        # если заказ еще не перешел к сборке
        if self.id and self.status < 2:
            self.total_amount = (
                self.cakes
                .aggregate(total_price=Sum('price'))['total_price']
            )
        super(Order, self).save(*args, **kwargs)

    def get_order_states(self):
        return self.ORDER_STATES

    def __str__(self):
        return f'Заказ {self.id} на сумму {self.total_amount}'
