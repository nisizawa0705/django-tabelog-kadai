from django import forms
from .models import StoreReview,MemberInfo,Reservation,CreditCard
from django.contrib.auth.hashers import make_password

#レビュー記載フォーム
class ReviewForm(forms.ModelForm):
    class Meta:
        model = StoreReview
        fields = ['star_num', 'com']
        widgets = {
            'com': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter your review here...'}),
        }
        #フィールドの表示名称指定
        labels = {
            'star_num': '',
            'com': 'レビューコメント',
        }

#ログインフォーム
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

#会員情報登録フォーム
class MemberInfoForm(forms.ModelForm):
    class Meta:
        model = MemberInfo
        fields = ['name', 'email', 'password', 'postal_number', 'address', 'phone_number']
        widgets = {
            'password': forms.PasswordInput(),  # パスワードを非表示にする
        }
    
        #フィールドの表示名称指定
        labels = {
            'name': '名前',
            'email': 'メールアドレス',
            'password': 'パスワード',
            'postal_number': '郵便番号',
            'address': '住所',
            'phone_number': '電話番号',
        }

    def save(self, commit=True):
        # パスワードのハッシュ化処理
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])  # パスワードをハッシュ化
        if commit:
            user.save()
        return user

# 会員情報を編集するためのフォーム
class MemberEditForm(forms.ModelForm):
    class Meta:
        model = MemberInfo
        fields = ['name', 'postal_number', 'address', 'phone_number']  # 編集可能なフィールド
        #フィールドの表示名称指定
        labels = {
            'name': '名前',
            'postal_number': '郵便番号',
            'address': '住所',
            'phone_number': '電話番号',
        }

# 予約フォーム
#作成日 : 20241011
#更新日 : 20241011
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['reservation_date', 'num_people']
        widgets = {
            'reservation_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'reservation_date': '予約日時',
            'num_people': '人数',
        }

#クレジットカードフォーム
class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ['card_token']
        widgets = {
            'card_token': forms.HiddenInput(),  # カードトークンはStripeから取得するので隠します
        }

    def clean_card_token(self):
        # バリデーションをここで調整
        card_token = self.cleaned_data.get('card_token')
        if not card_token:
            raise forms.ValidationError("カードトークンが無効です。")
        return card_token