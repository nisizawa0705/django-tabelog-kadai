import stripe
from .models import Subscription, MemberStatus

stripe.api_key = "your_stripe_api_key"

def create_subscription(user, token):
    # Stripeでサブスクリプションを作成
    customer = stripe.Customer.create(
        email=user.email,
        source=token  # トークンを使用して顧客を作成
    )
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{'price': 'price_id_for_monthly_subscription'}]
    )
    
    # 自作のSubscriptionモデルに保存
    Subscription.objects.create(user=user, status='active', member_status=MemberStatus.objects.get(pk=2))
