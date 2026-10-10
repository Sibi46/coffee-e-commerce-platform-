import json
import uuid
from decimal import Decimal
from functools import wraps
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction, IntegrityError
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Product, Variant, SavedSelection, Address, Coupon, Order, OrderItem, Review, NewsletterSubscriber, Category

class APIError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status

def csrf_failure(request, reason=''):
    return JsonResponse({'error': 'Session verification failed. Refresh the page and try again.'}, status=403)

@ensure_csrf_cookie
def storefront(request):
    html = (settings.BASE_DIR / 'dist/index.html').read_text(encoding='utf-8')
    html = html.replace('href="style.css', 'href="/static/style.css').replace('src="app.js', 'src="/static/app.js')
    html = html.replace('href="design.css', 'href="/static/design.css')
    html = html.replace('src="assets/', 'src="/static/assets/')
    html = html.replace('</body>', '<script src="/static/backend.js"></script></body>')
    return HttpResponse(html)

def text(data, key, maximum=200, required=True):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value.strip()) > maximum or (required and not value.strip()):
        raise APIError(f'Please provide a valid {key.replace("_", " ")}.')
    return value.strip()

def email(data):
    value = text(data, 'email', 254).lower()
    try:
        validate_email(value)
    except ValidationError:
        raise APIError('Please enter a valid email address.')
    return value

def integer(value, lower, upper):
    if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
        raise APIError(f'Enter a whole number between {lower} and {upper}.')
    return value

def logged_in(request):
    if not request.user.is_authenticated:
        raise APIError('Please sign in to continue.', 401)

def selection(request):
    if request.user.is_authenticated:
        obj, _ = SavedSelection.objects.get_or_create(user=request.user)
        return {'cart': obj.cart, 'wishlist': obj.wishlist}
    return {'cart': request.session.get('cart', {}), 'wishlist': request.session.get('wishlist', [])}

def save_selection(request, data):
    if request.user.is_authenticated:
        SavedSelection.objects.update_or_create(user=request.user, defaults=data)
    else:
        request.session['cart'] = data['cart']
        request.session['wishlist'] = data['wishlist']

def product_json(p):
    return {'id': p.slug, 'name': p.name, 'cat': p.category, 'desc': p.description, 'variant': p.options_note,
            'price': str(p.price) if p.price is not None else None, 'stock': p.stock,
            'variants': [{'id': v.id, 'name': v.name, 'price': str(v.price), 'stock': v.stock} for v in p.variants.all() if v.active]}

def user_json(user):
    return {'email': user.email, 'name': user.first_name} if user.is_authenticated else None

def address_json(a):
    return {k: getattr(a, k) for k in ['id', 'name', 'line1', 'city', 'state', 'postcode', 'phone']}

def order_json(o):
    return {'reference': str(o.reference), 'status': o.get_status_display(), 'created_at': o.created_at.isoformat(),
            'total': str(o.total) if o.total is not None else None, 'tracking': o.tracking,
            'items': [{'name': i.product_name, 'variant': i.variant_name, 'quantity': i.quantity,
                       'unit_price': str(i.unit_price) if i.unit_price is not None else None} for i in o.items.all()]}

def coupon(code):
    c = Coupon.objects.filter(code__iexact=code, active=True).first()
    if not c or (c.expires_at and c.expires_at <= timezone.now()):
        raise APIError('This coupon is invalid or has expired.')
    return c

def merge_guest(request, guest):
    current = selection(request)
    for key, item in guest['cart'].items():
        if key not in current['cart']:
            current['cart'][key] = item
        else:
            current['cart'][key]['quantity'] = min(99, current['cart'][key]['quantity'] + item['quantity'])
    current['wishlist'] = list(dict.fromkeys(current['wishlist'] + guest['wishlist']))
    save_selection(request, current)

def rate_limit(request, action, limit):
    key = f'{action}:{request.META.get("REMOTE_ADDR", "unknown")}'
    attempts = cache.get(key, 0)
    if attempts >= limit:
        raise APIError('Too many attempts. Please try again in a few minutes.', 429)
    cache.set(key, attempts + 1, 300)

def require_method(request, methods):
    if request.method not in methods:
        raise APIError('Method not allowed.', 405)

def api(request, resource, item=None):
    try:
        data = {}
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and request.body:
            try:
                data = json.loads(request.body)
            except (ValueError, UnicodeDecodeError):
                raise APIError('Invalid JSON request.')
            if not isinstance(data, dict):
                raise APIError('Expected a JSON object.')
        result, status = dispatch(request, resource, item, data)
        response = JsonResponse(result, status=status)
        response['Cache-Control'] = 'no-store'
        return response
    except APIError as e:
        return JsonResponse({'error': e.message}, status=e.status)
    except (Product.DoesNotExist, Variant.DoesNotExist, Address.DoesNotExist, Order.DoesNotExist):
        return JsonResponse({'error': 'Item not found.'}, status=404)

def dispatch(request, resource, item, data):
    if resource == 'session':
        require_method(request, ['GET'])
        return {'csrf': get_token(request), 'user': user_json(request.user), **selection(request)}, 200
    if resource == 'products':
        require_method(request, ['GET'])
        qs = Product.objects.filter(active=True).prefetch_related('variants')
        if item:
            return product_json(qs.get(slug=item)), 200
        if request.GET.get('category'):
            qs = qs.filter(category=request.GET['category'])
        if request.GET.get('q'):
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=request.GET['q']) | Q(description__icontains=request.GET['q']))
        return {'products': [product_json(p) for p in qs],
                'categories': [{'slug': c.slug, 'name': c.name, 'image': c.image.url if c.image else None} for c in Category.objects.all()]}, 200
    if resource in ['register', 'login']:
        require_method(request, ['POST'])
        rate_limit(request, resource, 15)
        address = email(data)
        if len(address) > 150:
            raise APIError('Account email must be at most 150 characters.')
        password = text(data, 'password', 128)
        guest = selection(request) if not request.user.is_authenticated else {'cart': {}, 'wishlist': []}
        if resource == 'register':
            user = get_user_model()(username=address, email=address, first_name=text(data, 'name', 100))
            try:
                validate_password(password, user)
            except ValidationError as e:
                raise APIError(' '.join(e.messages))
            try:
                with transaction.atomic():
                    user.set_password(password)
                    user.save()
            except IntegrityError:
                raise APIError('An account with this email already exists.')
        else:
            user = authenticate(request, username=address, password=password)
            if user is None:
                raise APIError('Email or password is incorrect.', 401)
        login(request, user)
        merge_guest(request, guest)
        return {'user': user_json(user), 'csrf': get_token(request), **selection(request)}, 200
    if resource == 'logout':
        require_method(request, ['POST'])
        logout(request)
        return {'user': None, 'csrf': get_token(request), **selection(request)}, 200
    if resource == 'cart':
        require_method(request, ['GET', 'POST', 'DELETE'])
        current = selection(request)
        if request.method != 'GET':
            p = Product.objects.get(slug=text(data, 'product'), active=True)
            if request.method == 'DELETE':
                current['cart'].pop(p.slug, None)
            else:
                qty = integer(data.get('quantity'), 1, 99)
                v = None
                if data.get('variant') is not None:
                    v = Variant.objects.get(pk=integer(data['variant'], 1, 2**31), product=p, active=True)
                current['cart'][p.slug] = {'quantity': qty, 'variant': v.id if v else None}
            save_selection(request, current)
        return current, 200
    if resource == 'wishlist':
        require_method(request, ['GET', 'POST', 'DELETE'])
        current = selection(request)
        if request.method != 'GET':
            p = Product.objects.get(slug=text(data, 'product'), active=True)
            if request.method == 'POST' and p.slug not in current['wishlist']:
                current['wishlist'].append(p.slug)
            if request.method == 'DELETE':
                current['wishlist'] = [s for s in current['wishlist'] if s != p.slug]
            save_selection(request, current)
        return current, 200
    if resource == 'addresses':
        logged_in(request)
        require_method(request, ['GET', 'POST', 'PUT', 'DELETE'])
        qs = Address.objects.filter(user=request.user)
        if request.method == 'GET':
            return {'addresses': [address_json(a) for a in qs]}, 200
        if item:
            a = qs.get(pk=integer_id(item))
        else:
            if request.method != 'POST':
                raise APIError('Address ID is required.')
            a = Address(user=request.user)
        if request.method == 'DELETE':
            a.delete()
            return {'deleted': True}, 200
        for field, maximum in [('name',100),('line1',200),('city',100),('state',100),('postcode',10),('phone',20)]:
            setattr(a, field, text(data, field, maximum))
        a.save()
        return address_json(a), 201
    if resource == 'coupon':
        require_method(request, ['POST'])
        c = coupon(text(data, 'code', 40))
        return {'code': c.code, 'percent': c.percent}, 200
    if resource == 'checkout':
        logged_in(request)
        require_method(request, ['POST'])
        return checkout_order(request, data), 201
    if resource == 'orders':
        logged_in(request)
        require_method(request, ['GET'])
        qs = Order.objects.filter(user=request.user).prefetch_related('items')
        if item:
            try:
                ref = uuid.UUID(item)
            except ValueError:
                raise APIError('Item not found.', 404)
            return order_json(qs.get(reference=ref)), 200
        return {'orders': [order_json(o) for o in qs]}, 200
    if resource == 'newsletter':
        require_method(request, ['POST'])
        rate_limit(request, 'newsletter', 20)
        NewsletterSubscriber.objects.get_or_create(email=email(data))
        return {'message': 'You are subscribed to product updates.'}, 201
    if resource == 'reviews':
        require_method(request, ['GET', 'POST'])
        p = Product.objects.get(slug=item or text(data, 'product'), active=True)
        if request.method == 'GET':
            return {'reviews': [{'name': r.user.first_name, 'rating': r.rating, 'text': r.text} for r in
                    Review.objects.filter(product=p, approved=True).select_related('user')]}, 200
        logged_in(request)
        Review.objects.update_or_create(user=request.user, product=p, defaults={'rating': integer(data.get('rating'),1,5),
                                        'text': text(data, 'text', 2000), 'approved': False})
        return {'message': 'Thank you. Your review is awaiting moderation.'}, 201
    raise APIError('Endpoint not found.', 404)

def integer_id(value):
    try:
        return integer(int(value), 1, 2**31)
    except (TypeError, ValueError):
        raise APIError('Invalid ID.')

@transaction.atomic
def checkout_order(request, data):
    try:
        key = uuid.UUID(text(data, 'checkout_key', 36))
    except ValueError:
        raise APIError('Invalid checkout key.')
    # Lock the customer row so repeat requests cannot create duplicate orders.
    get_user_model().objects.select_for_update().get(pk=request.user.pk)
    existing = Order.objects.filter(user=request.user, checkout_key=key).first()
    if existing:
        return order_json(existing)
    current = selection(request)
    if not current['cart']:
        raise APIError('Your bag is empty.')
    a = Address.objects.get(pk=integer(data.get('address_id'), 1, 2**31), user=request.user)
    entries = []
    subtotal = Decimal('0')
    enquiry = False
    for slug, entry in current['cart'].items():
        p = Product.objects.select_for_update().get(slug=slug, active=True)
        v = Variant.objects.select_for_update().get(pk=entry['variant'], product=p, active=True) if entry['variant'] else None
        if p.variants.filter(active=True).exists() and not v:
            raise APIError(f'Please choose an option for {p.name}.')
        price, stock = (v.price, v.stock) if v else (p.price, p.stock)
        quantity = integer(entry['quantity'], 1, 99)
        if price is None:
            enquiry = True
        elif stock < quantity:
            raise APIError(f'{p.name} does not have enough stock for this quantity.')
        else:
            subtotal += price * quantity
        entries.append((p, v, quantity, price))
    code = text(data, 'coupon', 40, required=False)
    c = coupon(code) if code else None
    if c and enquiry:
        raise APIError('Coupons apply once all selected products have confirmed prices.')
    discount = (subtotal * Decimal(c.percent) / 100).quantize(Decimal('0.01')) if c else Decimal('0')
    order = Order.objects.create(user=request.user, customer_name=a.name, email=request.user.email,
        address=address_json(a), note=text(data,'note',2000,required=False), checkout_key=key,
        status='enquiry' if enquiry else 'pending', subtotal=None if enquiry else subtotal,
        discount=discount, total=None if enquiry else subtotal-discount, coupon_code=c.code if c else '')
    for p, v, qty, price in entries:
        OrderItem.objects.create(order=order, product=p, product_name=p.name, variant_name=v.name if v else '', quantity=qty, unit_price=price)
        if not enquiry:
            target = v or p
            target.stock -= qty
            target.save(update_fields=['stock'])
    save_selection(request, {'cart': {}, 'wishlist': current['wishlist']})
    return order_json(order)
