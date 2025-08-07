from django.core.management.base import BaseCommand
from payments.models import TokenPackage

class Command(BaseCommand):
    help = 'Create sample token packages'

    def handle(self, *args, **options):
        # Clear existing packages
        TokenPackage.objects.all().delete()
        
        packages = [
            {
                'name': 'Starter Pack',
                'description': 'Perfect for occasional printing needs',
                'token_count': 50,
                'price': 50.00,
                'bonus_tokens': 0,
                'sort_order': 1,
                'is_active': True,
                'is_featured': False
            },
            {
                'name': 'Regular Pack',
                'description': 'Great value for regular users',
                'token_count': 100,
                'price': 95.00,
                'bonus_tokens': 5,
                'sort_order': 2,
                'is_active': True,
                'is_featured': True
            },
            {
                'name': 'Student Pack',
                'description': 'Bulk package for students with bonus tokens',
                'token_count': 200,
                'price': 180.00,
                'bonus_tokens': 20,
                'sort_order': 3,
                'is_active': True,
                'is_featured': False
            },
            {
                'name': 'Professional Pack',
                'description': 'High volume package for professionals',
                'token_count': 500,
                'price': 425.00,
                'bonus_tokens': 75,
                'sort_order': 4,
                'is_active': True,
                'is_featured': False
            },
            {
                'name': 'Enterprise Pack',
                'description': 'Maximum value package with huge bonus',
                'token_count': 1000,
                'price': 800.00,
                'bonus_tokens': 200,
                'sort_order': 5,
                'is_active': True,
                'is_featured': False
            }
        ]
        
        for package_data in packages:
            package = TokenPackage.objects.create(**package_data)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created package: {package.name} - {package.total_tokens} tokens for ₹{package.price}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(packages)} token packages')
        )
