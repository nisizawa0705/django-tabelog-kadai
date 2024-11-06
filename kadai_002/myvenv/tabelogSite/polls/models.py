from django.db import models
from django.utils import timezone   #現在時刻を取得する。
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model

#会員ステータス(有料 or 無料)
class MemberStatus(models.Model):
    name = models.CharField(max_length=200)
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.name

# CustomUserManagerの実装 ユーザーを正しく作成するために、CustomUserManagerが必要
# createsuperuserコマンドやユーザー作成時にこれらのメソッドが呼ばれる
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        通常のユーザーを作成する
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        #ユーザーインスタンスを作成
        user = self.model(email=email, **extra_fields)
        #パスワードをハッシュ化してユーザーインスタンスにセット
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        スーパーユーザーを作成する
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

#会員情報
class MemberInfo(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    postal_number = models.CharField(max_length=8)
    address = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    member_status = models.ForeignKey('MemberStatus', on_delete=models.CASCADE, default=1)
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    is_active = models.BooleanField(default=True)   #ユーザーアカウントが有効かどうかを表します。
    is_staff = models.BooleanField(default=False)    #ユーザーがスタッフ（管理者画面にアクセスできるユーザー）かどうかを表します。(全ての操作を行えるわけではない。)

    objects = CustomUserManager()  # カスタムマネージャーを指定

    USERNAME_FIELD = 'email'  # メールアドレスでログイン
    REQUIRED_FIELDS = []  # 他に必須フィールドがない場合は空のリスト

    class Meta:
        verbose_name = "会員"  # 単数形の表示名
        verbose_name_plural = "会員管理"  # 複数形の表示名（管理画面の表示名）

    def __str__(self):
        return self.name

#クレジットカード情報(アップグレード用)
#作成日 : 20241008
#更新日 : 20241011
class CreditCard(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    last_four_digits = models.CharField(max_length=4)   # カード番号の最後の4桁
    card_brand = models.CharField(max_length=50)    # カードのブランド（Visa, MasterCardなど）
    card_token = models.CharField(max_length=255)  # Stripeのカードトークン
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.card_brand} **** **** {self.last_four_digits}"
    
#サブスクリプション(アップグレード用)
#作成日 : 20241008
#更新日 : 20241011
class Subscription(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=255)   #Stripeが提供するサブスクリプションの一意の識別ID
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive'), ('canceled', 'Canceled')],
        default='active'
    )  # サブスクリプションの状態
    member_status = models.ForeignKey(MemberStatus, on_delete=models.CASCADE)   #有料会員、無料会員などのユーザーのステータスを保存。
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.status}"

#カテゴリ
class Category(models.Model):
    name = models.CharField(max_length=200)
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)
    
    class Meta:
        verbose_name = "カテゴリ"  # 単数形の表示名
        verbose_name_plural = "カテゴリ管理"  # 複数形の表示名（管理画面の表示名）

    def __str__(self):
        return self.name

#店舗情報
class StoreInfo(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    # img = models.ImageField(blank=True, default='noImage.png')
    img = models.ImageField(upload_to='images/')
    description = models.TextField(blank=True, null=True)
    price_top = models.PositiveIntegerField()
    price_bottom = models.PositiveIntegerField()
    open_time = models.TimeField(verbose_name="営業開始時間")
    close_time = models.TimeField(verbose_name="営業終了時間")
    postal_number = models.CharField(max_length=8)
    address = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = "店舗"  # 単数形の表示名
        verbose_name_plural = "店舗管理"  # 複数形の表示名（管理画面の表示名）
    
    def __str__(self):
        return self.name

#レビュー
class StoreReview(models.Model):
    member_id = models.ForeignKey(MemberInfo, on_delete=models.CASCADE)
    store_id = models.ForeignKey(StoreInfo, on_delete=models.CASCADE)
    star_num = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])  # 星の数（1〜5）
    com = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return f"{self.store_id.name} - {self.star_num} Stars"
    
#お気に入り
#作成日 : 20241009
#更新日 : 20241009
class FaboriteStore(models.Model):
    member_id = models.ForeignKey(MemberInfo, on_delete=models.CASCADE)
    store_id = models.ForeignKey(StoreInfo, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

#予約関連
#作成日 : 20241011
#更新日 : 20241011
class Reservation(models.Model):
    member_id = models.ForeignKey(MemberInfo, on_delete=models.CASCADE)
    store_id = models.ForeignKey(StoreInfo, on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(verbose_name="予約日")
    num_people = models.PositiveIntegerField(verbose_name="人数")
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return f"Reservation by {self.member_id.name} at {self.store_id.name} for {self.num_people} people"
    
#会社概要
#作成日 : 20241027
#更新日 : 20241027
class CompanyInfo(models.Model):
    name = models.CharField(max_length=255, verbose_name="会社名")
    address = models.CharField(max_length=255, verbose_name="所在地")
    ceo = models.CharField(max_length=255, verbose_name="代表者")
    established_date = models.DateField(verbose_name="設立年月日")
    capital = models.CharField(max_length=50, verbose_name="資本金")
    business_content = models.TextField(verbose_name="事業内容")
    employee_count = models.PositiveIntegerField(verbose_name="従業員数")
    created_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = "会社概要"
        verbose_name_plural = "会社概要管理"

    def __str__(self):
        return self.name