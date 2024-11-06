from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView,ListView,DetailView,CreateView,UpdateView,DeleteView,View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required   #レビュー登録で使用するデコーダのインポート
from django.contrib.auth import views as auth_views
from django.utils.http import urlsafe_base64_decode  # 会員登録のメール認証用
from django.contrib.auth import get_user_model  # 会員登録のメール認証用
from django.contrib.auth.tokens import default_token_generator  # 会員登録のメール認証用
from .utils import send_verification_email  # 会員登録のメール認証用(メール送信用関数をインポート)
from .models import Category,StoreInfo,StoreReview,MemberInfo,CreditCard,Subscription,FaboriteStore,Reservation,MemberStatus,CompanyInfo
from .forms import ReviewForm, LoginForm, MemberInfoForm, MemberEditForm,ReservationForm,CreditCardForm
from django.urls import reverse_lazy,reverse
from django.utils import timezone
from django.views.generic import DetailView, UpdateView
from .services import create_subscription   #クレカ用
import stripe   #クレカ用
from django.conf import settings    #設定ファイル読込

class TopView(TemplateView):
    template_name = "top.html"

# 店舗一覧ビュー
class StoreDispView(LoginRequiredMixin,ListView):
    model = StoreInfo

    # テンプレートに渡す追加のコンテキストデータを設定
    # カテゴリを同じHTML内に取得することが目的。ListViewクラスを使用すると複数のクラスを取得できないためこれを追加する必要がある。
    def get_queryset(self):
        queryset = super().get_queryset()
        # URLパラメータから選択されたカテゴリと検索ワードを取得
        selected_categories = self.request.GET.getlist('categories')
        search_word = self.request.GET.get('search_word', '')
        # カテゴリが選択されている場合、プロダクトをそのカテゴリでフィルタリング
        if selected_categories:
            queryset = queryset.filter(category__id__in=selected_categories)
        # 検索ワードでフィルタリング（名前に部分一致するプロダクトを表示）
        if search_word:
            queryset = queryset.filter(name__icontains=search_word)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()  # 全てのカテゴリを渡す
        context['selected_categories'] = self.request.GET.getlist('categories')  # 選択されたカテゴリを渡す
        context['search_word'] = self.request.GET.get('search_word', '')  # 検索ワードを渡す
        return context

# 店舗詳細ビュー
class ProductDetailView(DetailView):
    model = StoreInfo
    template_name = 'product_detail.html'  # 詳細表示用のテンプレート
    context_object_name = 'storeInfo'  # テンプレートで使用するコンテキスト名。テンプレートでは「storeInfo.name」などで呼び出せるようになる。

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = ReviewForm()  # フォームをコンテキストに追加
        context['reviews'] = StoreReview.objects.filter(store_id=self.object)  # プロダクトに関連するレビューを取得
        # 現在のユーザーがこの店舗をお気に入りに登録しているかどうかを確認
        context['is_favorite'] = FaboriteStore.objects.filter(member_id=self.request.user, store_id=self.object).exists()
        context["star_range"] = range(1,6)
        return context

# 新しいレビューを追加する処理
# デコレーターを使って、ユーザーがログインしていなければレビューを投稿できないようにしています。
@login_required  # ユーザーがログインしていることを保証
def add_review(request, pk):
    storeInfo = get_object_or_404(StoreInfo, pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.store_id = storeInfo  # レビューにプロダクトを紐付け
            review.member_id = request.user  # レビューにログインユーザーを紐付け
            review.save()
            return redirect('product_detail', pk=storeInfo.pk)  # 詳細ページにリダイレクト

    return redirect('product_detail', pk=storeInfo.pk)

# レビュー編集用ビュー
class EditReviewView(UserPassesTestMixin, UpdateView):
    model = StoreReview
    form_class = ReviewForm
    template_name = 'edit_review.html'
    pk_url_kwarg = 'review_pk'  # URLのreview_pkを使ってレビューを取得する

    def get_success_url(self):
        # 編集後にリダイレクトするページ（店舗の詳細ページへ）
        store_pk = self.object.store_id.pk  # レビューに関連付けられた店舗のpkを取得
        return reverse_lazy('product_detail', kwargs={'pk': store_pk})

    def test_func(self):
        # ログインユーザーがレビューの投稿者であることを確認
        review = self.get_object()
        return self.request.user == review.member_id

# レビュー削除用ビュー
class DeleteReviewView(UserPassesTestMixin, DeleteView):
    model = StoreReview
    template_name = 'delete_review_confirm.html'
    pk_url_kwarg = 'review_pk'

    def get_success_url(self):
        # 削除後にリダイレクトするページ（店舗の詳細ページへ）
        return reverse_lazy('product_detail', kwargs={'pk': self.kwargs['pk']})

    def test_func(self):
        # ログインユーザーがレビューの投稿者であることを確認
        review = self.get_object()
        return self.request.user == review.member_id

#ログインビュー
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # 認証を行う
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('top')  # ログイン後のリダイレクト先(top画面にリダイレクトする。)
            else:
                form.add_error(None, 'メールアドレスまたはパスワードが間違っています。')
    else:
        form = LoginForm()

    #ログインページのテンプレートにフォームオブジェクトを渡して表示する処理です。
    return render(request, 'login.html', {'form': form})

#パスワードリセットビュー
class PasswordResetView(auth_views.PasswordResetView):
    email_template_name = 'password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    template_name = 'password_reset.html'

class PasswordResetDone(auth_views.PasswordResetDoneView):
    # パスワード変更用URL送信完了ページ
    template_name = "password_reset_done.html"

class PasswordResetConfirm(auth_views.PasswordResetConfirmView):
    # 新パスワード入力用ページ
    success_url = reverse_lazy("password_reset_complete")
    template_name = "password_reset_confirm.html"

class PasswordResetComplete(auth_views.PasswordResetCompleteView):
    # 新パスワード設定完了ページ
    template_name = "password_reset_complete.html"

#マイページビュー
class MypageView(LoginRequiredMixin, DetailView):
    model = MemberInfo
    template_name = "my_page.html"
    context_object_name = 'user'

    def get_object(self):
        # 現在のログインユーザーを取得
        return self.request.user

    def get_context_data(self, **kwargs):
        # 親クラスのコンテキストデータを取得
        context = super().get_context_data(**kwargs)
        # お気に入り店舗を取得してコンテキストに追加
        context['favorites'] = FaboriteStore.objects.filter(member_id=self.request.user)
        context['cards'] = CreditCard.objects.filter(user=self.request.user)
        return context

#会員登録ビュー
class MemberRegistrationView(CreateView):
    model = MemberInfo
    form_class = MemberInfoForm
    template_name = 'member_registration.html'
    success_url = reverse_lazy('registration_temporary')  # 登録完了ページのURL

    def form_valid(self, form):
        # ユーザーの一時保存（非アクティブ状態）
        user = form.save(commit=False)
        user.is_active = False  # 初期状態を非アクティブに
        user.save()
        
        # 認証メールを送信
        send_verification_email(user)
        
        # フォームが有効な場合の処理を継承元に委ねる
        #return super().form_valid(form)
        return redirect(self.success_url)

# メール認証用のURLにアクセスした際にユーザーを有効化する処理。
def verify_email(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    print(f"このユーザーを使用 : {user}")  # ユーザーのデバッグ出力
    print(f"このトークンを使用 : {token}")  # トークンのデバッグ出力
    print(f"このuidb64を使用 : {uidb64}")  # uidb64のデバッグ出力
    print(f"check_token : {default_token_generator.check_token(user, token)}")  # check_tokenのデバッグ出力

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('registration_success')
    else:
        return redirect('registration_failed')

def registration_failed(request):
    return render(request, 'registration_failed.html')

def registration_temporary(request):
    return render(request, 'registration_temporary.html')

def registration_success(request):
    return render(request, 'registration_success.html')

# 会員情報を表示するクラスベースのビュー
class ProfileView(LoginRequiredMixin, DetailView):
    model = MemberInfo
    template_name = 'profile.html'
    context_object_name = 'user'

    def get_object(self):
        # 現在のログインユーザーを取得
        return self.request.user
    
# 会員情報を編集するクラスベースのビュー
class EditProfileView(LoginRequiredMixin, UpdateView):
    model = MemberInfo
    form_class = MemberEditForm
    template_name = 'edit_profile.html'
    success_url = reverse_lazy('profile')  # 編集後にプロフィールページへリダイレクト

    def get_object(self):
        # 現在のログインユーザーを取得
        return self.request.user
    
#クレジットカード関連(アップグレード用)
#作成日 : 20241008
#更新日 : 20241023(クレジットカード情報の編集がうまくいってなかったため修正)
stripe.api_key = settings.STRIPE_SECRET_KEY  # Stripe APIキーの設定

# クレジットカードの登録
class CreditCardCreateView(CreateView):
    model = CreditCard
    form_class = CreditCardForm
    template_name = 'creditcard_create.html'
    success_url = reverse_lazy('top')   # 登録成功時のURLの設定

    def form_valid(self, form):
        # JavaScriptで生成されたStripeトークンを取得
        token = self.request.POST.get('card_token')

        print(f"Received stripe token: {token}")  # トークンのデバッグ出力

        # トークンがない場合、エラーメッセージを表示
        if not token:
            form.add_error(None, "カード情報の取得に失敗しました。再度入力してください。")
            return self.form_invalid(form)

        try:
            # 既にトークンが使用されていないかチェック（省略可能）
            if CreditCard.objects.filter(card_token=token).exists():
                form.add_error(None, "このトークンは既に使用されています。新しいカード情報を入力してください。")
                return self.form_invalid(form)
            
            # Stripeで顧客を作成
            customer = stripe.Customer.create(
                email=self.request.user.email
            )

            # PaymentMethodを顧客にアタッチする
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={'token': token}
            )
            stripe.PaymentMethod.attach(
                payment_method.id,
                customer=customer.id
            )

            # サブスクリプションを作成（PaymentMethodを指定）
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'plan': settings.STRIPE_PLAN_ID}],
                default_payment_method=payment_method.id  # 明示的にPaymentMethodを指定
            )

            # クレジットカード情報を保存
            last_four = payment_method.card.last4
            card_brand = payment_method.card.brand
            form.instance.user = self.request.user
            form.instance.card_token = payment_method.id  # カードトークンではなくPaymentMethodのIDを保存
            form.instance.last_four_digits = last_four
            form.instance.card_brand = card_brand

            # サブスクリプションモデルを保存
            Subscription.objects.create(
                user=self.request.user,
                stripe_subscription_id=subscription.id,
                status='active',
                member_status=MemberStatus.objects.get(pk=2)  # 有料会員のステータスを設定
            )

            # ユーザーのステータスを有料会員に更新
            self.request.user.member_status = MemberStatus.objects.get(pk=2)
            self.request.user.save()

        except stripe.error.StripeError as e:
            form.add_error(None, f"Stripe APIエラーが発生しました: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY  # 公開APIキーを追加
        return context

# クレジットカード情報の編集
class CreditCardUpdateView(UpdateView):
    model = CreditCard
    form_class = CreditCardForm
    template_name = 'creditcard_update.html'
    success_url = reverse_lazy('top')

    def form_valid(self, form):
        token = self.request.POST.get('card_token')

        print(f"Received stripe token: {token}")  # トークンのデバッグ出力

        if not token:
            form.add_error(None, "カード情報の取得に失敗しました。再度入力してください。")
            return self.form_invalid(form)

        try:
            # 顧客をメールアドレスで検索して取得
            customers = stripe.Customer.list(email=self.request.user.email).data

            if customers:
                customer = customers[0]
            else:
                customer = stripe.Customer.create(email=self.request.user.email)

            # 古いクレジットカードのPaymentMethodをリスト化する。あとで削除する時に使用。
            old_payment_methods = stripe.PaymentMethod.list(
                customer=customer.id,
                type="card"
            )

            # 新しいPaymentMethodを作成
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={'token': token}
            )
            print(f"New payment_method.id: {payment_method.id}")    # payment_method.id確認

            # 新しいPaymentMethodを顧客にアタッチ
            stripe.PaymentMethod.attach(payment_method.id, customer=customer.id)

            # 特定のPaymentMethodを使ってサブスクリプションの支払いを行うように更新
            # この処理を入れないと支払方法が「デフォルトの支払い方法に請求」になってしまう。
            subscriptions = stripe.Subscription.list(customer=customer.id, status='active').data
            for subscription in subscriptions:
                stripe.Subscription.modify(
                    subscription.id,
                    default_payment_method=payment_method.id  # 特定の支払い方法に請求
                )
                print(f"Subscription updated with new payment method: {subscription.id}")

            # 古いクレジットカードのPaymentMethodをデタッチ（必要に応じて）
            for old_pm in old_payment_methods.data:
                if old_pm.id != payment_method.id:
                    print(f"Old payment_method.id: {old_pm.id}")    # payment_method.id確認
                    stripe.PaymentMethod.detach(old_pm.id)

            # クレジットカード情報を保存
            form.instance.user = self.request.user
            form.instance.card_token = payment_method.id  # 新しいPaymentMethod IDを保存
            form.instance.last_four_digits = payment_method.card.last4
            form.instance.card_brand = payment_method.card.brand

            # 保存内容出力
            print(f"New self.request.user: {self.request.user}")
            print(f"New payment_method.id: {payment_method.id}")
            print(f"New payment_method.card.last4: {payment_method.card.last4}")
            print(f"New payment_method.card.brand: {payment_method.card.brand}")

        except stripe.error.StripeError as e:
            form.add_error(None, f"Stripe APIエラーが発生しました: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        return context

# クレジットカードの削除
class CreditCardDeleteView(DeleteView):
    model = CreditCard
    template_name = 'cancel_subscription.html'
    success_url = reverse_lazy('top')

    def get_queryset(self):
        print("get_querysetメソッドが呼ばれました")
        return CreditCard.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        print("postメソッドが呼ばれました")
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        print("deleteメソッドが呼ばれました")
        # 削除するカードを取得
        self.object = self.get_object()
        user = self.request.user

        # 通常の削除処理
        response = super().delete(request, *args, **kwargs)

        # 削除されたクレジットカードに紐づくサブスクリプションを取得
        subscription = Subscription.objects.filter(
            user=user,
            status='active'
        ).first()

        if subscription:
            try:
                # Stripe APIキーを設定
                stripe.api_key = settings.STRIPE_SECRET_KEY

                # サブスクリプションがこのクレジットカードに紐づいているか確認するためにStripeサブスクリプション情報を取得
                stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

                # サブスクリプションの支払いに使用されているクレジットカード情報と、削除対象のクレジットカードが一致するかを確認
                if stripe_subscription.default_payment_method == self.object.card_token:
                    # サブスクリプションをキャンセル
                    stripe.Subscription.delete(subscription.stripe_subscription_id)
                    print(f"Stripeサブスクリプション {subscription.stripe_subscription_id} がキャンセルされました。")

                    # モデルからも削除
                    subscription.delete()
                    print("サブスクリプションがモデルから削除されました。")
                else:
                    print("このサブスクリプションは削除するクレジットカードに紐づいていません。")

            except Exception as e:
                print(f"Stripeサブスクリプションのキャンセルに失敗しました: {e}")

        # 残りのクレジットカードの数を確認し、0枚なら会員ステータスを無料会員に変更
        remaining_cards = CreditCard.objects.filter(user=user).count()
        if remaining_cards == 0:
            print("会員ステータスを無料会員に変更します。")
            user.member_status = MemberStatus.objects.get(pk=1)
            user.save()

        return response

#お気に入り関連
#作成日 : 20241009
#更新日 : 20241009
@login_required
def add_favorite(request, store_id):
    store = get_object_or_404(StoreInfo, id=store_id)
    favorite, created = FaboriteStore.objects.get_or_create(member_id=request.user, store_id=store)
    
    if not created:
        # 既にお気に入りに登録されていた場合
        favorite.delete()

        # リファラーを取得
        referer = request.META.get('HTTP_REFERER')

        # リファラーに応じてリダイレクト先を決定
        if 'my_page' in referer:
            return redirect('my_page')  # マイページからのリダイレクト
        else:
            return redirect('product_detail', pk=store_id)  # 店舗詳細ページからのリダイレクト
    
    # 新しくお気に入りに追加した場合のリダイレクト先
    return redirect('product_detail', pk=store_id)


# 予約関連
#作成日 : 20241011
#更新日 : 20241023(営業時間外エラー、現在より前の日時エラーを追加)
# 予約作成ビュー
class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'create_reservation.html'
    
    def form_valid(self, form):
        # 予約日時が現在よりも前の場合はエラーにする
        reservation_date = form.cleaned_data.get('reservation_date')
        current_time = timezone.now()
        if reservation_date < current_time:
            form.add_error('reservation_date', "現在より前の日時は入力できません。")
            return self.form_invalid(form)

        # 店舗情報を取得
        store = StoreInfo.objects.get(pk=self.kwargs['store_id'])

        # 営業時間を取得
        open_time = reservation_date.replace(
            hour=store.open_time.hour,
            minute=store.open_time.minute,
            second=0,
            microsecond=0
        )
        close_time = reservation_date.replace(
            hour=store.close_time.hour,
            minute=store.close_time.minute,
            second=0,
            microsecond=0
        )

        # 営業時間内かどうかをチェック
        if not (open_time <= reservation_date <= close_time):
            form.add_error('reservation_date', f"当店の営業時間内での入力をお願いいたします。（{store.open_time.strftime('%H:%M')}〜{store.close_time.strftime('%H:%M')}）")
            return self.form_invalid(form)

        # ログインしているユーザーを予約者として設定
        form.instance.member_id = self.request.user
        # 店舗情報を設定
        form.instance.store_id = StoreInfo.objects.get(pk=self.kwargs['store_id'])
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = StoreInfo.objects.get(pk=self.kwargs['store_id'])
        return context

    def get_success_url(self):
        return reverse_lazy('reservation_list')

# 予約一覧ビュー
class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'reservation_list.html'
    
    def get_queryset(self):
        return Reservation.objects.filter(member_id=self.request.user).order_by('-reservation_date')

# 予約キャンセルビュー
class ReservationCancelView(LoginRequiredMixin, DeleteView):
    
    model = Reservation
    template_name = 'reservation_cancel_confirm.html'
    success_url = reverse_lazy('reservation_list')

    def get_queryset(self):
        return Reservation.objects.filter(member_id=self.request.user)  # ログインユーザーの予約のみ削除可能
    
#会社概要
#作成日 : 20241027
#更新日 : 20241027
class CompanyInfoView(DetailView):
    model = CompanyInfo
    template_name = 'company_info.html'

    def get_object(self, queryset=None):
        # モデルが単一レコードであることを想定して最初のレコードを取得
        return CompanyInfo.objects.first()