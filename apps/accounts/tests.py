from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import CustomUserCreationForm, CustomUserChangeForm


# Create your tests here.
class SignupPageTests(TestCase):
    username = "newuser"
    email = "newuser@email.com"
    level = "beginner"

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
            self.username, self.email, self.level
        )
        self.assertEqual(get_user_model().objects.all().count(), 1)
        self.assertEqual(get_user_model().objects.all()[0].username, self.username)
        self.assertEqual(get_user_model().objects.all()[0].email, self.email)
        self.assertEqual(get_user_model().objects.all()[0].level, self.level)


class CustomUserModelTest(TestCase):
    def test_default_level_is_beginner(self):
        user = get_user_model().objects.create_user(
            username="testuser", password="password123"
        )
        self.assertEqual(user.level, get_user_model().BEGINNER)

    def test_all_valid_values(self):
        User = get_user_model()
        for level in [User.BEGINNER, User.INTERMEDIATE, User.ADVANCED]:
            user = User.objects.create_user(
                username=f"testuser_{level}", password="password123", level=level
            )
            self.assertEqual(user.level, level)


class CustomUserCreationFormTest(TestCase):
    def test_custom_user_creation_form_valid_data(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "S3curePa$$word!",
            "password2": "S3curePa$$word!",
            "level": "beginner",  # カスタムフィールドであるlevelをテスト
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid_data(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "S3curePa$$word!",
            "password2": "S3curePa$$word!",
            "level": "invalid_level",  # 無効なレベルを設定
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("level", form.errors)  # levelフィールドにエラーがあることを確認

    def test_custom_user_creation_form_invalid_password(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "123",  # 短すぎるパスワード
            "password2": "123",
            "level": "beginner",
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
            level="beginner",
        )
        form_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "level": "intermediate",
        }
        form = CustomUserChangeForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

        # 変更を保存して、保存された結果を確認
        updated_user = form.save()
        self.assertEqual(updated_user.username, "testuser")
        self.assertEqual(updated_user.email, "testuser@example.com")
        self.assertEqual(updated_user.level, "intermediate")
