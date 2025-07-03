from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

GENERAL = CustomUser.UserRole.GENERAL
LIBRARIAN = CustomUser.UserRole.LIBRARIAN


# Create your tests here.
class CustomUserAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # テスト用のスーパーユーザーを作成
        cls.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123",
        )

    def setUp(self):
        self.client.login(username="admin", password="password123")

    def test_user_role_display_in_admin(self):
        # 新規ユーザーを作成
        user = get_user_model().objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="password123",
        )

        # 管理画面のユーザー詳細ページにアクセス
        response = self.client.get(
            reverse("admin:accounts_customuser_change", args=[user.id])
        )

        # ユーザー詳細画面に「role」フィールドが表示されていることを確認
        self.assertContains(response, "role")
        self.assertContains(response, GENERAL)

    def test_admin_can_update_user_role(self):
        # テスト対象ユーザーを作成
        user = get_user_model().objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="password123",
        )

        # 管理画面のユーザー変更 URL を生成
        url = reverse("admin:accounts_customuser_change", args=[user.id])

        # 現在のフォーム内容を GET で取得
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # フォームの初期データを取得
        form = response.context["adminform"].form
        form_data = form.initial

        # role を LIBRARIAN に変更
        form_data["role"] = LIBRARIAN

        # 重要：他の必須フィールドを含める（admin画面で必要なすべて）
        form_data.update(
            {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "date_joined_0": user.date_joined.strftime("%Y-%m-%d"),
                "date_joined_1": user.date_joined.strftime("%H:%M:%S"),
            }
        )
        # None の値を削除
        form_data.pop("last_login", None)
        if user.last_login:
            form_data.update(
                {
                    "last_login_0": user.last_login.strftime("%Y-%m-%d"),
                    "last_login_1": user.last_login.strftime("%H:%M:%S"),
                }
            )

        # POST リクエストを送信
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # ユーザーの role を検証
        user.refresh_from_db()
        self.assertEqual(user.role, LIBRARIAN)


class SignupPageTests(TestCase):
    username = "newuser"
    email = "newuser@email.com"
    role = GENERAL

    def test_signup_page_status_code(self):
        response = self.client.get("/accounts/signup/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_by_name(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")

    def test_signup_form(self):
        new_user = get_user_model().objects.create_user(
            self.username, self.email, self.role
        )
        self.assertEqual(get_user_model().objects.all().count(), 1)
        self.assertEqual(get_user_model().objects.all()[0].username, self.username)
        self.assertEqual(get_user_model().objects.all()[0].email, self.email)
        self.assertEqual(get_user_model().objects.all()[0].role, self.role)


class CustomUserModelTest(TestCase):
    def test_default_role_is_general(self):
        user = get_user_model().objects.create_user(
            username="testuser", password="password123"
        )
        self.assertEqual(user.role, GENERAL)

    def test_all_valid_values(self):
        User = get_user_model()
        for role in [
            GENERAL,
            LIBRARIAN,
        ]:
            user = User.objects.create_user(
                username=f"testuser_{role}", password="password123", role=role
            )
            self.assertEqual(user.role, role)


class CustomUserCreationFormTest(TestCase):
    def test_custom_user_creation_form_valid_data(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "S3curePa$$word!",
            "password2": "S3curePa$$word!",
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid_password(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "123",  # 短すぎるパスワード
            "password2": "123",
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)  # password2 にエラーがあることを確認

        self.assertIn(
            "This password is too short. It must contain at least 8 characters.",
            str(form.errors["password2"]),
        )


class CustomUserChangeFormTest(TestCase):
    def test_custom_user_change_form_valid_data(self):
        user = get_user_model().objects.create_user(
            username="newuser",
            email="newuser@email.com",
            password="S3curePa$$word!",
            role=GENERAL,
        )
        form_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "role": LIBRARIAN,
        }
        form = CustomUserChangeForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

        # 変更を保存して、保存された結果を確認
        updated_user = form.save()
        self.assertEqual(updated_user.username, "testuser")
        self.assertEqual(updated_user.email, "testuser@example.com")
        self.assertEqual(updated_user.role, LIBRARIAN)
