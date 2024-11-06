from django.contrib import admin
from .models import MemberInfo,MemberStatus,Category,StoreInfo,StoreReview,FaboriteStore,Reservation,CreditCard,Subscription,CompanyInfo


#admin.site.register(MemberStatus)
#admin.site.register(Subscription)
#admin.site.register(CreditCard)
admin.site.register(CompanyInfo)


# 【店舗情報】
@admin.register(StoreInfo)
class StoreInfoAdmin(admin.ModelAdmin):
    # 表示するフィールド
    list_display = ('name', 'category', 'phone_number', 'address', 'created_date', 'update_date')
    
    # 検索フィールド
    search_fields = ('name', 'phone_number', 'address')

    # 編集可能なフィールド
    list_editable = ('phone_number', 'address')

    # ソート順
    ordering = ('-created_date',)

    # ページネーションの設定
    list_per_page = 20

    # 詳細ページに表示するフィールド（update_dateを削除）
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'description', 'price_top', 'price_bottom', 'open_time', 'close_time', 'postal_number', 'address', 'phone_number', 'img')
        }),
        ('日時', {
            'fields': ('created_date',),
            'classes': ('collapse',),
        }),
    )
    
    # 日付フィルター
    list_filter = ('created_date', 'category')

    # フィールドの編集ができないものを指定（update_dateを含む）
    readonly_fields = ('created_date', 'update_date')
    

# 【カテゴリ情報】
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_date', 'update_date')  # 一覧で表示するフィールド
    search_fields = ('name',)  # 検索可能なフィールド

admin.site.register(Category, CategoryAdmin)


# 【会員情報】
class MemberInfoAdmin(admin.ModelAdmin):
    # 管理画面のリストで表示するフィールドを指定
    list_display = ('name', 'email', 'postal_number', 'phone_number', 'member_status', 'is_active', 'created_date')

    # 管理画面で検索できるフィールドを指定
    search_fields = ('email', 'name')

    # 管理画面でフィルタリングできるフィールドを指定（オプション）
    list_filter = ('member_status', 'is_active', 'created_date')

    # デフォルトの並び順を指定（オプション）
    ordering = ('-created_date',)

# MemberInfoモデルを管理画面に登録
admin.site.register(MemberInfo, MemberInfoAdmin)
