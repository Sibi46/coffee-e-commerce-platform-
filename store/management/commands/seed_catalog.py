from django.core.management.base import BaseCommand
from store.models import Product

class Command(BaseCommand):
    help = 'Add the supplied client catalog without inventing prices or overwriting admin changes.'
    def handle(self, *args, **options):
        rows = [
            ('instant-coffee','Premium Instant Coffee','coffee','Premium Instant Coffee (In different flavors).','Flavor selection to be confirmed'),
            ('ctc-tea','Strong Premium CTC Tea','tea','Strong Premium CTC Tea.','Pack sizes to be confirmed'),
            ('mustard-oil','Cold Pressed Mustard Oil','edible-oils','Premium Cold Pressed Mustard Oil. Locally manufactured.','Bottle sizes to be confirmed'),
            ('blend-coffee','Arabica + Robusta Blend','coffee','Blended Coffee (Arabica + Robusta).','Pack sizes to be confirmed'),
            ('ctc-blend','Premium CTC Blend','tea','Premium CTC Blend.','Pack sizes to be confirmed'),
            ('masala-tea','Premium Masala Tea','tea','Premium Masala Tea.','Pack sizes to be confirmed'),
            ('green-tea','Green Tea','tea','Green Tea.','Pack sizes to be confirmed'),
            ('cappuccino','Cappuccino Premix','coffee','Cappuccino Premix.','Pack sizes to be confirmed')]
        for slug,name,category,description,note in rows:
            Product.objects.get_or_create(slug=slug, defaults={'name':name,'category':category,'description':description,'options_note':note})
        self.stdout.write(self.style.SUCCESS('Client catalog seeded. Prices remain unconfigured.'))
