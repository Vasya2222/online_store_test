from django.db import models


# Create your models here.


class Item(models.Model):
    """
    Модель товара.

    Поля:
        name (CharField) — название товара, до 20 символов.
        description (TextField) — подробное описание товара.
        price (PositiveIntegerField) — цена товара в целых единицах валюты.
        currency (CharField) — валюта цены: 'USD' или 'EUR'.
    """

    name = models.CharField(max_length=20)
    description = models.TextField()
    price = models.PositiveIntegerField()
    currency = models.CharField(
        max_length=20,
        choices=[('USD', 'usd'), ('EUR', 'eur')],
        blank=True
    )

    def __str__(self):
        return f"{self.name} — {self.price}"

class Discount(models.Model):
    """
    Модель скидки.

    Поля:
        name (CharField) — название скидки, до 20 символов.
        amount_off (PositiveIntegerField) — фиксированная сумма скидки (в целых единицах), если применяется.
        percent_off (PositiveIntegerField) — процент скидки, если применяется.
        stripe_coupon_id (CharField) — идентификатор купона в Stripe, связанного со скидкой.
    """

    name = models.CharField(max_length=20)
    amount_off = models.PositiveIntegerField(blank=True, null=True)
    percent_off = models.PositiveIntegerField(blank=True, null=True)
    stripe_coupon_id = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        if self.percent_off:
            return f"{self.name} — {self.percent_off}% off"
        elif self.amount_off:
            return f"{self.name} — {self.amount_off} off"
        return self.name




from django.db import models


class Tax(models.Model):
    """
    Модель налога.

    Поля:
        name (CharField) — название налога, до 20 символов.
        percentage (PositiveIntegerField) — процент налога (целое число).
        inclusive (BooleanField) — является ли налог включённым в цену.
        stripe_tax_rate_id (CharField) — идентификатор налоговой ставки в Stripe.
    """

    name = models.CharField(max_length=20)
    percentage = models.PositiveIntegerField()
    inclusive = models.BooleanField()
    stripe_tax_rate_id = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"{self.name} — {self.percentage}%"


class Order(models.Model):
    """
    Модель заказа.

    Поля:
        items (ManyToManyField[Item]) — список товаров в заказе.
        discount (ForeignKey[Discount]) — применённая скидка (если есть).
        tax (ForeignKey[Tax]) — применённый налог (если есть).
        paid (BooleanField) — статус оплаты (True — оплачен, False — не оплачен).
    """

    items = models.ManyToManyField("Item")
    discount = models.ForeignKey("Discount", on_delete=models.CASCADE, blank=True, null=True)
    tax = models.ForeignKey("Tax", on_delete=models.CASCADE, blank=True, null=True)
    paid = models.BooleanField(blank=True)

    def __str__(self):
        return f"Order #{self.id} — {self.items.count()} items — {'Paid' if self.paid else 'Not Paid'}"

