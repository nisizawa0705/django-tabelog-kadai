from django.contrib.auth.backends import ModelBackend
from .models import MemberInfo  # カスタムユーザーモデルをインポート
from django.core.exceptions import ObjectDoesNotExist

class EmailBackend(ModelBackend):
    """
    カスタム認証バックエンド。
    メールアドレスとパスワードでログインできるようにする。
    ログインビューで呼び出される。
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # メールアドレスでユーザーを検索
            user = MemberInfo.objects.get(email=username)
            # パスワードが一致しているか確認
            if user.check_password(password):  # パスワードのハッシュを比較
                return user
        except MemberInfo.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return MemberInfo.objects.get(pk=user_id)
        except MemberInfo.DoesNotExist:
            return None