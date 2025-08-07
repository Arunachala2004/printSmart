#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

def test_dashboard_data():
    """Test dashboard data retrieval"""
    try:
        from users.models import User
        from files.models import File
        from print_jobs.models import PrintJob
        from payments.models import Payment
        from django.db.models import Sum
        
        print("🧪 Testing Dashboard Data...")
        
        # Get admin user
        try:
            user = User.objects.get(username='admin')
            print(f"✅ User found: {user.username}")
            print(f"✅ Wallet balance: ${user.wallet_balance}")
        except User.DoesNotExist:
            print("❌ Admin user not found!")
            return False
        
        # Test File model
        try:
            total_files = File.objects.filter(user=user).count()
            print(f"✅ Total files: {total_files}")
        except Exception as e:
            print(f"❌ Error getting files: {e}")
        
        # Test PrintJob model
        try:
            total_print_jobs = PrintJob.objects.filter(user=user).count()
            completed_jobs = PrintJob.objects.filter(user=user, status='completed').count()
            pending_jobs = PrintJob.objects.filter(user=user, status='pending').count()
            print(f"✅ Print jobs - Total: {total_print_jobs}, Completed: {completed_jobs}, Pending: {pending_jobs}")
        except Exception as e:
            print(f"❌ Error getting print jobs: {e}")
        
        # Test Payment model
        try:
            total_spent = Payment.objects.filter(
                user=user, 
                payment_type='debit',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            print(f"✅ Total spent: ${total_spent}")
        except Exception as e:
            print(f"❌ Error getting payments: {e}")
        
        # Test recent data
        try:
            recent_print_jobs = PrintJob.objects.filter(user=user).order_by('-created_at')[:5]
            recent_files = File.objects.filter(user=user).order_by('-created_at')[:5]
            print(f"✅ Recent data - Jobs: {len(recent_print_jobs)}, Files: {len(recent_files)}")
        except Exception as e:
            print(f"❌ Error getting recent data: {e}")
        
        print("\n🎉 Dashboard data test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_dashboard_data()
