"""
Cart implemented as a session-based Python class.
No database model needed - stored in request.session.
"""
from decimal import Decimal
from django.conf import settings
from products.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def prune_invalid_products(self):
        """Drop cart lines for deleted or inactive products.

        Not called from __init__: this instantiates on every page via the
        cart context processor, and pruning does a DB query, so it only
        runs where the cart contents are actually displayed or mutated.
        """
        if not self.cart:
            return
        product_ids = [pid for pid in self.cart if str(pid).isdigit()]
        if not product_ids:
            return
        valid_ids = {
            str(product_id)
            for product_id in Product.objects.filter(
                id__in=product_ids,
                is_active=True,
            ).values_list('id', flat=True)
        }
        stale_ids = [pid for pid in self.cart if pid not in valid_ids]
        for product_id in stale_ids:
            del self.cart[product_id]
        if stale_ids:
            self.save()

    def add(self, product, quantity=1, metal='', ring_size='', override_qty=False):
        """Add/update a cart line. Returns status dict for UX messaging."""
        product_id = str(product.id)
        if product.stock <= 0:
            if product_id in self.cart:
                del self.cart[product_id]
                self.save()
            return {
                'ok': False,
                'out_of_stock': True,
                'clamped': False,
                'quantity': 0,
            }

        requested = quantity
        prev_qty = self.cart.get(product_id, {}).get('quantity', 0)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'name': product.name,
                'slug': product.slug,
                'metal': metal,
                'ring_size': ring_size,
            }
        elif metal or ring_size:
            # Refresh options on subsequent adds when provided
            if metal:
                self.cart[product_id]['metal'] = metal
            if ring_size:
                self.cart[product_id]['ring_size'] = ring_size

        if override_qty:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        clamped = False
        if self.cart[product_id]['quantity'] > product.stock:
            self.cart[product_id]['quantity'] = product.stock
            clamped = True

        if self.cart[product_id]['quantity'] <= 0:
            del self.cart[product_id]
            self.save()
            return {
                'ok': False,
                'out_of_stock': product.stock <= 0,
                'clamped': True,
                'quantity': 0,
            }

        self.save()
        final_qty = self.cart[product_id]['quantity']
        return {
            'ok': True,
            'out_of_stock': False,
            'clamped': clamped or (not override_qty and final_qty < prev_qty + requested),
            'quantity': final_qty,
            'stock': product.stock,
        }
    def save(self):
        self.session.modified = True

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}
        for item_id, item in self.cart.items():
            item = item.copy()
            product = product_map.get(item_id)
            if product:
                item['product'] = product
                item['total_price'] = Decimal(item['price']) * item['quantity']
                yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()
