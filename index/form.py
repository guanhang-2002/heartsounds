from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import widgets, ModelForm
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from .utils import *
from . import utils
from .models import *


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = widgets.TextInput(
            attrs={'placeholder': "username", "class": "form-control"})
        self.fields['email'].widget = widgets.EmailInput(
            attrs={'placeholder': "email", "class": "form-control"})
        self.fields['password1'].widget = widgets.PasswordInput(
            attrs={'placeholder': "password", "class": "form-control"})
        self.fields['password2'].widget = widgets.PasswordInput(
            attrs={'placeholder': "repeat password", "class": "form-control"})

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise ValidationError("该邮箱已经存在.")
        return email

    class Meta:
        model = get_user_model()
        fields = ("username", "email")


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = widgets.TextInput(
            attrs={'placeholder': "username", "class": "form-control"})
        self.fields['password'].widget = widgets.PasswordInput(
            attrs={'placeholder': "password", "class": "form-control"})


class ForgetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="新密码",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                'placeholder': "密码"
            }
        ),
    )
    new_password2 = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                'placeholder': "确认密码"
            }
        ),
    )
    code = forms.CharField(
        label='验证码',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': "验证码"
            }
        ),
    )

    def clean_new_password2(self):
        password1 = self.data.get("new_password1")
        password2 = self.data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("两次密码不一致")
        password_validation.validate_password(password2)

        return password2

    email = forms.EmailField(
        label='邮箱',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': "邮箱"
            }
        ),
        validators=[]
    )
    # def clean_code(self):
    #     code = self.cleaned_data.get("code")
    #     error = utils.verify(
    #         email=self.cleaned_data.get("email"),
    #         code=code,
    #     )
    #     if error:
    #         raise ValidationError(error)
    #     return code


class ForgetPasswordCodeForm(forms.Form):
    email = forms.EmailField(
        label='邮箱',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': "邮箱"
            }
        ),
        validators=[]
    )

    def clean_email(self):
        user_email = self.cleaned_data.get("email")
        if not Users.objects.filter(
                email=user_email
        ).exists():
            # todo 这里的报错提示可以判断一个邮箱是不是注册过，如果不想暴露可以修改
            raise ValidationError("未找到邮箱对应的用户")
        return user_email


class UploadeForm(ModelForm):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),  # 支持多文件上传
        label='心音数据',
        help_text='最大100M',
    )

    class Meta:
        model = Introduce
        fields = ['sample_from', 'duration_for_sample', 'style_of_sampling', 'sample_frequency']
        # duration_for_sample 的帮助文字在introducemodel已经定义
        help_texts = {'style_of_sampling': '如 心尖瓣', 'sample_frequency': '如 5Hz'}

    def clean_sample_frequency(self):
        sample_frequency = self.cleaned_data.get('sample_frequency')
        result = re_match_for_sample_frequency(sample_frequency)
        if result is None:
            raise ValidationError('请以Hz为单位输入时长')
        return result

    def clean_duration_for_sample(self):
        sample_duration = self.cleaned_data.get('duration_for_sample')
        result = re_match_for_sample_duration(sample_duration)
        if result is None:
            raise ValidationError('请把采样时间转化为秒后输入')
        return result
