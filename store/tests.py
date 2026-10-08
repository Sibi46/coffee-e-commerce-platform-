import json
import uuid
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Product, Variant, Address, Order, Coupon, Review, NewsletterSubscriber

class StoreTests(TestCase):
    def setUp(self):
        cache.clear()
        self.product = Product.objects.create(slug='coffee', name='Coffee', category='coffee', description='Coffee')
        self.user = get_user_model().objects.create_user('test@example.com','test@example.com','Str0ng-test-pass!',first_name='Test')
        self.other = get_user_model().objects.create_user('other@example.com','other@example.com','Str0ng-test-pass!')
        self.address = Address.objects.create(user=self.user,name='Test',line1='Street',city='Dehradun',state='Uttarakhand',postcode='248003',phone='1234567890')
    def post(self, path, data, client=None):
        return (client or self.client).post('/api/'+path+'/',json.dumps(data),content_type='application/json')
    def add(self, qty=1, variant=None):
        return self.post('cart',{'product':'coffee','quantity':qty,'variant':variant})
    def checkout(self, key=None, **extra):
        return self.post('checkout',{'address_id':self.address.id,'checkout_key':str(key or uuid.uuid4()),**extra})
    def test_catalog_filters_and_hidden_products(self):
        Product.objects.create(slug='hidden',name='Hidden',category='tea',description='',active=False)
        self.assertEqual(len(self.client.get('/api/products/').json()['products']),1)
        self.assertEqual(self.client.get('/api/products/?category=tea').json()['products'],[])
        self.assertEqual(len(self.client.get('/api/products/?q=Coffee').json()['products']),1)
        self.assertEqual(self.client.get('/api/products/hidden/').status_code,404)
    def test_registration_password_hashing_and_guest_merge(self):
        self.add(2)
        self.post('wishlist',{'product':'coffee'})
        response=self.post('register',{'email':'new@example.com','name':'New','password':'New-str0ng-pass!456'})
        self.assertEqual(response.status_code,200)
        user=get_user_model().objects.get(username='new@example.com')
        self.assertTrue(user.check_password('New-str0ng-pass!456'))
        self.assertNotEqual(user.password,'New-str0ng-pass!456')
        self.assertEqual(response.json()['cart']['coffee']['quantity'],2)
        self.post('logout',{})
        result=self.post('login',{'email':'new@example.com','password':'New-str0ng-pass!456'})
        self.assertEqual(result.json()['wishlist'],['coffee'])
    def test_login_and_weak_password_validation(self):
        self.assertEqual(self.post('login',{'email':self.user.email,'password':'wrong'}).status_code,401)
        self.assertEqual(self.post('register',{'email':'new@example.com','name':'New','password':'12345678'}).status_code,400)
        self.assertEqual(self.client.get('/api/register/').status_code,405)
    def test_csrf_is_required_for_mutations(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(self.post('cart',{'product':'coffee','quantity':1},c).status_code,403)
        token=c.get('/api/session/').json()['csrf']
        response=c.post('/api/cart/',json.dumps({'product':'coffee','quantity':1}),content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200)
    def test_quantity_and_variant_validation(self):
        for qty in [0,100,-1,1.2,True,'3']:
            self.assertEqual(self.add(qty).status_code,400)
        another=Product.objects.create(slug='tea',name='Tea',category='tea',description='Tea')
        variant=Variant.objects.create(product=another,name='250g',price='100.00',stock=10)
        self.assertEqual(self.add(1,variant.id).status_code,404)
    def test_customer_address_and_order_isolation(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get('/api/addresses/').json()['addresses'],[])
        self.assertEqual(self.client.delete(f'/api/addresses/{self.address.id}/',content_type='application/json').status_code,404)
        self.add()
        self.assertEqual(self.checkout().status_code,404)
        o=Order.objects.create(user=self.user,customer_name='Test',email=self.user.email)
        self.assertEqual(self.client.get(f'/api/orders/{o.reference}/').status_code,404)
    def test_unpriced_checkout_saves_enquiry_and_is_idempotent(self):
        self.client.force_login(self.user)
        self.add(3)
        key=uuid.uuid4()
        response=self.checkout(key)
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json()['status'],'Availability enquiry')
        self.assertIsNone(response.json()['total'])
        self.assertEqual(self.checkout(key).json()['reference'],response.json()['reference'])
        self.assertEqual(Order.objects.count(),1)
        self.assertEqual(Order.objects.first().items.get().quantity,3)
        self.assertEqual(self.client.get('/api/cart/').json()['cart'],{})
        self.assertEqual(self.checkout().status_code,400)
    def test_priced_checkout_reserves_stock_and_recalculates_coupon(self):
        self.client.force_login(self.user)
        self.product.price=Decimal('125.50');self.product.stock=5;self.product.save()
        Coupon.objects.create(code='SAVE',percent=10)
        self.add(2)
        response=self.checkout(coupon='SAVE',total='1.00')
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json()['total'],'225.90')
        self.assertEqual(response.json()['status'],'Pending confirmation')
        self.product.refresh_from_db();self.assertEqual(self.product.stock,3)
    def test_out_of_stock_checkout_is_atomic(self):
        self.client.force_login(self.user)
        self.product.price=Decimal('10');self.product.stock=1;self.product.save()
        self.add(2)
        self.assertEqual(self.checkout().status_code,400)
        self.assertEqual(Order.objects.count(),0)
        self.assertEqual(self.client.get('/api/cart/').json()['cart']['coffee']['quantity'],2)
    def test_variant_checkout_uses_variant_price_and_stock(self):
        self.client.force_login(self.user)
        v=Variant.objects.create(product=self.product,name='250g',price='150',stock=3)
        self.add();self.assertEqual(self.checkout().status_code,400)
        self.add(2,v.id)
        response=self.checkout();self.assertEqual(response.json()['total'],'300.00')
        v.refresh_from_db();self.assertEqual(v.stock,1)
        self.assertEqual(Order.objects.get().items.get().variant_name,'250g')
    def test_expired_coupon_and_review_moderation(self):
        Coupon.objects.create(code='OLD',percent=10,expires_at=timezone.now()-timedelta(days=1))
        self.assertEqual(self.post('coupon',{'code':'OLD'}).status_code,400)
        self.assertEqual(self.post('reviews',{'product':'coffee','rating':5,'text':'Good'}).status_code,401)
        self.client.force_login(self.user)
        self.assertEqual(self.post('reviews',{'product':'coffee','rating':5,'text':'Good'}).status_code,201)
        self.assertEqual(self.client.get('/api/reviews/coffee/').json()['reviews'],[])
        Review.objects.update(approved=True)
        self.assertEqual(self.client.get('/api/reviews/coffee/').json()['reviews'][0]['text'],'Good')
    def test_newsletter_validation_dedup_and_malformed_json(self):
        self.assertEqual(self.post('newsletter',{'email':'bad'}).status_code,400)
        self.post('newsletter',{'email':'person@example.com'});self.post('newsletter',{'email':'person@example.com'})
        self.assertEqual(NewsletterSubscriber.objects.count(),1)
        response=self.client.post('/api/cart/','[1]',content_type='application/json')
        self.assertEqual(response.status_code,400)
    def test_storefront_connects_backend(self):
        response=self.client.get('/')
        self.assertContains(response,'/static/backend.js')
        self.assertContains(response,'/static/style.css')
        self.assertIn('csrftoken',response.cookies)
