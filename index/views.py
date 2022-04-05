import logging
import os

import requests
from django.contrib import auth
from django.conf import settings
from django.contrib.auth import logout, login, authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, FileResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import urlquote
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView, DetailView, ListView
from .models import Users, HeartSounds, Introduce
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_job
from .form import RegisterForm, LoginForm, ForgetPasswordForm, ForgetPasswordCodeForm, UploadeForm
from .models import Users
from django.views import View
from . import utils
from .utils import get_sha256, send_email, generate_code

logger = logging.getLogger('file')
maillogger = logging.getLogger('mail')


def index(request):
    # try:
    #     scheduler = BackgroundScheduler()
    #     scheduler.add_jobstore(DjangoJobStore(), "default")
    #     job = scheduler.add_job(hello, 'interval', seconds=1)
    #     scheduler.start()
    # except Exception as e:
    #     scheduler.shutdown()
    # maillogger.error("the program's pre_test")
    # logger.error('test runaps')
    return render(request, 'index.html', locals())


class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'register.html'

    # @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(RegisterView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        if form.is_valid():
            user = form.save(False)
            user.is_active = True
            user.save(True)
            content = """<p>感谢您注册HeartSounds数据库</p>"""
            send_email(
                emailto=[
                    user.email,
                ],
                title='HeartSounds',
                content=content)
            logout(self.request)
            # Delete(user.username)
            logger.info(f'user{user.username}register')
            return redirect(reverse('index:login'))
        else:
            return self.render_to_response({
                'form': form
            })


# 暂时删除Uesr
def Delete(username):
    Users.objects.filter(username=username).delete()


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'login.html'
    success_url = '/'
    login_ttl = 60 * 60 * 24  # 一天的时间

    # @method_decorator(sensitive_post_parameters('password'))
    # @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form = AuthenticationForm(data=self.request.POST, request=self.request)
        if self.request.session.get('has_login'):
            return render(self.request,'index.html',context={'repeatloginmessage':'你不能重复登录'})
        elif form.is_valid():
            active_user = form.get_user()
            auth.login(self.request, active_user)
            self.request.session.set_expiry(0)
            self.request.session['has_login']=True
            logger.info(f'{self.request.user.username} login')

            return super(LoginView, self).form_valid(form)
        else:
            return self.render_to_response({
                'form': form
            })


class LogoutView(RedirectView):
    url = '/'

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(LogoutView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        logger.info(f'user{self.request.user.username}logout')
        logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class ForgetPasswordView(FormView):
    form_class = ForgetPasswordForm
    template_name = 'forget_password.html'

    def form_valid(self, form):

        if form.is_valid():
            email = form.cleaned_data['email']
            code = cache.get(email)

            if code != form.cleaned_data['code']:
                return HttpResponse('验证码错误')
            else:
                user = Users.objects.filter(email=email).get()
                logger.info(f'{user}repeatpassword-code:{code}')
                user.password = make_password(form.cleaned_data["new_password2"])
                user.save()
                return HttpResponseRedirect('/')
        else:
            return self.render_to_response({'form': form})


class ForgetPasswordEmailCodeView(View):

    def post(self, request):
        form = ForgetPasswordCodeForm(request.POST)
        if not form.is_valid():
            return HttpResponse("错误的邮箱")
        to_email = form.cleaned_data["email"]
        code = generate_code()
        utils.send_verify_email(to_email, code)
        utils.set_code(to_email, code)

        return redirect(reverse('index:forgetpassword'))

    def get(self, request):
        form = ForgetPasswordCodeForm()
        return render(request, 'forget_password_code.html', locals())


class UploadView(FormView):
    form_class = UploadeForm
    template_name = 'upload.html'

    def dispatch(self, request, *args, **kwargs):
        return super(UploadView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if form.is_valid() and self.request.user.is_authenticated:
            files = self.request.FILES.getlist('file')
            # 获取心音信息
            sample_from = form.cleaned_data['sample_from']
            duration_for_sample = form.cleaned_data['duration_for_sample']
            style_of_sampling = form.cleaned_data['style_of_sampling']
            sample_frequency = form.cleaned_data['sample_frequency']
            # 获取所属用户信息
            owner_id = self.request.user.id

            for f in files:
                destination_name = os.path.join(settings.MEDIA_ROOT, f.name)
                destination = open(destination_name, 'wb+')
                heartsounds = HeartSounds(name=f.name, owner_id=owner_id, file_path=destination_name)
                heartsounds.save()
                introduce = Introduce(name=f.name,
                                      heartSounds=heartsounds,
                                      sample_frequency=sample_frequency,
                                      duration_for_sample=duration_for_sample,
                                      style_of_sampling=style_of_sampling,
                                      sample_from=sample_from)
                introduce.save()
                logger.info(f"user-id{owner_id} upload_file {f.name}")
                for chunk in f.chunks():
                    destination.write(chunk)
                destination.close()
            return redirect(reverse('index:file_list', args=[1, ]))
            # 返回上传页
        return self.render_to_response({'form': form})


class HeartSoundsDemonstrate(DetailView):
    template_name = 'file_detail.html'
    pk_url_kwarg = 'id'
    model = HeartSounds
    context_object_name = 'heartsounds_list'


class HeartSoundsList(ListView):
    template_name = 'heartsounds_list.html'
    paginate_by = 8
    model = Introduce
    context_object_name = 'heartsounds_introduce_list'


@login_required()
def download(request, id):
    try:
        file = HeartSounds.objects.get(id=id)
        destination=file.file_path
        with open(destination,'rb') as f:
            logger.info(f"{request.user} download {destination} file")
            response = HttpResponse(f)
            response['Content-type']="application/octet-stream"
            response['Content-Disposition'] = 'attachment;filename='+os.path.basename(destination)
            return response
    except Exception as e:
        logger.error('数据库文件丢失或损坏')
        message = '您下载的文件已损坏'
        return render(request, 'downFileError.html', {'message': message})
