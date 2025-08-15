import os
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
import stripe

from .models import Item, Order, Discount, Tax

stripe.api_key = settings.STRIPE_SECRET_KEY


def item_view(request, item_id):
    """
    Возвращает простую HTML-страницу с информацией о товаре и кнопкой Buy.

    Аргументы:
        request (HttpRequest) — объект запроса.
        item_id (int) — ID товара.

    Возвращает:
        HttpResponse с рендером шаблона "products/item_detail.html".
        В context передаются:
            - item: объект Item
            - stripe_publishable_key: публичный ключ Stripe
    """
    item = get_object_or_404(Item, id=item_id)
    context = {
        "item": item,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, "products/item_detail.html", context)


def buy_view(request, item_id):
    """
    Создаёт Stripe Checkout Session для покупки одного товара и возвращает session.id в JSON.

    Аргументы:
        request (HttpRequest) — объект запроса.
        item_id (int) — ID товара.

    Логика:
        - Формирует success и cancel URL.
        - Создаёт сессию Stripe с данными товара.
        - Возвращает JSON {"session_id": <id сессии>}.

    Возвращает:
        JsonResponse с ID сессии Stripe, либо HttpResponseBadRequest при ошибке.
    """
    item = get_object_or_404(Item, id=item_id)

    origin = request.build_absolute_uri("/")[:-1]
    success_url = origin + "/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = origin + f"/item/{item.id}/"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": item.currency,
                        "product_data": {
                            "name": item.name,
                            "description": item.description[:200],
                        },
                        "unit_amount": int(item.price * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except Exception as e:
        return HttpResponseBadRequest(f"Stripe error: {str(e)}")

    return JsonResponse({"session_id": session.id})


def order_view(request, order_id):
    """
    Возвращает HTML-страницу с информацией о корзине и кнопкой Buy.

    Аргументы:
        request (HttpRequest) — объект запроса.
        order_id (int) — ID заказа.

    Возвращает:
        HttpResponse с рендером шаблона "products/order_detail.html".
        В context передаются:
            - order: объект Order
            - stripe_publishable_key: публичный ключ Stripe
    """
    order = get_object_or_404(Order, id=order_id)
    context = {
        "order": order,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, "products/order_detail.html", context)


def buy_order_view(request, order_id):
    """
    Создаёт Stripe Checkout Session для покупки всех товаров из заказа и возвращает session.id в JSON.

    Аргументы:
        request (HttpRequest) — объект запроса.
        order_id (int) — ID заказа.

    Логика:
        - Формирует success и cancel URL.
        - Проверяет наличие скидки и создает купон в Stripe при необходимости.
        - Проверяет наличие налога и создает TaxRate в Stripe при необходимости.
        - Создаёт список line_items с товарами, налогами и скидками.
        - Создаёт Stripe Checkout Session и возвращает session_id.

    Возвращает:
        JsonResponse с ID сессии Stripe, либо HttpResponseBadRequest при ошибке.
    """
    order = get_object_or_404(Order, id=order_id)

    origin = request.build_absolute_uri("/")[:-1]
    success_url = origin + "/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = origin + f"/order/{order.id}/"

    # Проверка скидки
    if order.discount:
        discount = order.discount
        if not discount.stripe_coupon_id:
            if discount.amount_off:
                coupon_id = stripe.Coupon.create(
                    duration="once",
                    amount_off=discount.amount_off,
                    currency=order.items.first().currency
                )
            else:
                coupon_id = stripe.Coupon.create(
                    duration="once",
                    percent_off=discount.percent_off
                )
            discount.stripe_coupon_id = coupon_id['id']
            discount.save()
    else:
        discount = None

    # Проверка налога
    if order.tax:
        tax = order.tax
        if not tax.stripe_tax_rate_id:
            tax_id = stripe.TaxRate.create(
                display_name=tax.name,
                percentage=tax.percentage,
                inclusive=tax.inclusive
            )
            tax.stripe_tax_rate_id = tax_id['id']
            tax.save()
    else:
        tax = None

    # Создание line_items
    line_items = []
    for item in order.items.all():
        item_data = {
            "price_data": {
                "currency": item.currency,
                "product_data": {
                    "name": item.name,
                    "description": item.description,
                },
                "unit_amount": int(item.price * 100),
            },
            "quantity": 1,
        }
        if order.tax and order.tax.stripe_tax_rate_id:
            item_data["tax_rates"] = [order.tax.stripe_tax_rate_id]

        line_items.append(item_data)

    # Создание сессии
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except Exception as e:
        return HttpResponseBadRequest(f"Stripe error: {str(e)}")

    return JsonResponse({"session_id": session.id})
