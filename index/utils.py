import logging
import random
import string
import requests
import typing
import re
from datetime import timedelta
from fileinput import filename
import django.dispatch
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from hashlib import sha256
from django.utils import timezone
from django.contrib.sites.models import Site
from django.core.cache import cache


logger=logging.getLogger('file')
maillogger=logging.getLogger('mail')
send_email_signal = django.dispatch.Signal()
_code_ttl = timedelta(minutes=5)
def get_sha256(str):
    m = sha256(str.encode('utf-8'))
    return m.hexdigest()


def get_current_site(request):
    site = Site.objects.get_current(request)
    return site


def send_email(emailto, title, content):
    send_email_signal.send(
        send_email.__class__,
        emailto=emailto,
        title=title,
        content=content)


@receiver(send_email_signal)
def send_email_signal_handler(sender, **kwargs):
    emailto = kwargs['emailto']
    title = kwargs['title']
    content = kwargs['content']

    msg = EmailMultiAlternatives(
        title,
        content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=emailto)
    print()
    msg.content_subtype = "html"
    try:
        msg.send()
    except Exception as e:
        raise ValueError('邮箱发送失败')


def generate_code() -> str:
    """生成随机数验证码"""
    return ''.join(random.sample(string.digits, 6))


def send_verify_email(to_mail: str, code: str, subject: str = "邮件验证码"):
    """发送重设密码验证码
    Args:
        to_mail: 接受邮箱
        subject: 邮件主题
        code: 验证码
    """
    html_content = f"您正在重设密码，验证码为：{code}, {_code_ttl.seconds//60}分钟内有效，请妥善保管"
    send_email([to_mail], subject, html_content)

def set_code(email, code):
    """设置code"""
    cache.add(str(email), str(code),_code_ttl.seconds)

def get_code(email):
    """获取code"""
    return cache.get(email)

def re_match_for_sample_frequency(sample):
    """匹配输入的频率数据"""
    pattern=re.compile(r'\d+Hz',re.I)
    return re.match(pattern,sample).group()

def re_match_for_sample_duration(sample):
    """匹配输入的时间间隔数据"""
    pattern = re.compile(r'\d+s', re.I)
    return re.match(pattern, sample).string

