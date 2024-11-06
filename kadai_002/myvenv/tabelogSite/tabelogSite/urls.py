from django.contrib import admin
from django.urls import path
from polls import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.TopView.as_view(), name="top"),
    path('polls/', views.StoreDispView.as_view(), name="storeinfo"),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),  # 詳細ページへのパス

    #レビュー関連
    path('product/<int:pk>/add_review/', views.add_review, name='add_review'),  # レビュー追加
    path('product/<int:pk>/edit_review/<int:review_pk>/', views.EditReviewView.as_view(), name='edit_review'),  # レビュー編集
    path('product/<int:pk>/delete_review/<int:review_pk>/', views.DeleteReviewView.as_view(), name='delete_review'),    # レビュー削除

    #マイページ
    path('my_page/', views.MypageView.as_view(), name='my_page'),

    #お気に入り
    path('favorite/<int:store_id>/', views.add_favorite, name='add_favorite'),

    #会員登録
    # path('register/', views.member_registration, name='member_registration'),
    path('register/', views.MemberRegistrationView.as_view(), name='member_registration'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('register/temporary/', views.registration_temporary, name='registration_temporary'),
    path('register/success/', views.registration_success, name='registration_success'),
    path('registration-failed/', views.registration_failed, name='registration_failed'),

    #会員情報表示、編集
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),

    #パスワードリセット機能
    path('password_reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),

    #クレジットカード関連
    path('creditcard/create/', views.CreditCardCreateView.as_view(), name='creditcard_create'),
    path('creditcard/update/<int:pk>/', views.CreditCardUpdateView.as_view(), name='creditcard_update'),
    path('creditcard/delete/<int:pk>/', views.CreditCardDeleteView.as_view(), name='creditcard_confirm_delete'),

    #ログイン関連
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # ここを追加
    #path('login/', views.LoginView.as_view(), name="login"),
    #path('logout/', views.LogoutView.as_view(), name="logout"),

    #予約関連
    path('reservations/create/<int:store_id>/', views.ReservationCreateView.as_view(), name='create_reservation'),
    path('reservations/', views.ReservationListView.as_view(), name='reservation_list'),
    path('reservations/cancel/<int:pk>/', views.ReservationCancelView.as_view(), name='cancel_reservation'),

    #会社情報
    path('company-info/', views.CompanyInfoView.as_view(), name='company_info'),
]

#画像を取りに行く設定
if settings.DEBUG:
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
