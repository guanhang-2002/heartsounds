from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Users(AbstractUser):
    """
    继承Django的User类
    """
    CHOICES = (
        ('yes', 'Yes'),
        ('no', 'NO'),
    )
    is_professional = models.CharField(choices=CHOICES, max_length=4)
    photo = models.ImageField('头像', blank=True, upload_to='publicStatic/images/user_portrait',
                              default='publicStatic/images/user_portrait/default_user_protrait.jpg')


class HeartSounds(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=5000,default='暂无')
    file_path = models.CharField(max_length=100)
    created_time=models.DateTimeField('创建时间',default=timezone.now)
    owner = models.ForeignKey(Users, on_delete=models.CASCADE)

    def __str__(self):
        return self.description
    class Meta:
        verbose_name = '心音主体'
        verbose_name_plural = '心音主体'


class Introduce(models.Model):
    """数据的参数"""
    choices = (
        ('male', 'male'),
        ('female', 'female'),
        ('child', 'child'),
    )
    name=models.CharField(max_length=50)
    heartSounds = models.ForeignKey(HeartSounds, on_delete=models.CASCADE)
    sample_from = models.CharField('采样来源', choices=choices, max_length=10)
    duration_for_sample = models.CharField('采样时间', help_text='请采用秒数为计时单位',max_length=20)
    style_of_sampling = models.CharField('采样方式', max_length=50)
    sample_frequency = models.CharField('采样频率', max_length=50)

    def __str__(self):
        return self.heartSounds.description

    class Meta:
        verbose_name = '心音介绍'
        verbose_name_plural = '心音介绍'


class Dynamic(models.Model):
    """数据库的动态字段"""
    heartSounds = models.ForeignKey(HeartSounds, on_delete=models.CASCADE)
    count_for_download = models.IntegerField(default=0)
    dynamicPicture = models.ImageField('心音动图,暂未实现', default=r"C:\Users\guanh\Desktop\temptest.jpg")

    class Meta:
        verbose_name = '心音动态部分'
        verbose_name_plural = '心音动态部分'

class PopuOfScience(models.Model):
    """科普部分"""
    heartSounds=models.ForeignKey(HeartSounds,on_delete=models.CASCADE)
    # 科普描述文本.
    text=models.TextField(default='暂时还没有科普文本',max_length=3000)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name="心音科普"
        verbose_name_plural="心音科普"



# 以下是测试用例
"""
kwargs1={ 'heartSounds':Heart, 'sample_from':'male','duration_for_sample':[1],'style_of_sampling':'随机采样','sample_frequency':'5hz'}
"""
"""
 kwargs={'name':'tset1','description':'This is a test program',file_path':'C:\HeartSound','owner':admin,}
"""