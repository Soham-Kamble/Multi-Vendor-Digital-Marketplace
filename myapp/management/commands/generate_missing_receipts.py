from django.core.management.base import BaseCommand
from myapp.models import OrderDetail
from myapp.views import generate_receipt


class Command(BaseCommand):
    help = 'Generate receipts for paid orders missing receipt files'

    def handle(self, *args, **options):
        qs = OrderDetail.objects.filter(has_paid=True).filter(receipt__isnull=True)
        total = qs.count()
        self.stdout.write(self.style.NOTICE(f'Found {total} paid orders without receipts'))
        success = 0
        failed = 0
        for order in qs:
            try:
                self.stdout.write(f'Generating receipt for order {order.id}...')
                generate_receipt(order)
                success += 1
                self.stdout.write(self.style.SUCCESS(f'OK: {order.id}'))
            except Exception as e:
                failed += 1
                self.stderr.write(f'FAILED: {order.id} -> {e}')

        self.stdout.write(self.style.SUCCESS(f'Done. success={success} failed={failed}'))
