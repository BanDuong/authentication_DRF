from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, BaseUserManager, UserManager, Group, Permission, \
    PermissionsMixin
from django.utils.translation import gettext as _


# Create your models here.

class Questions(models.Model):
    question = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class Answers(models.Model):
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)
    answer = models.CharField(max_length=100)
    image = models.ImageField(null=True, blank=True, upload_to="media/")
    created_at = timezone.now()

    def __str__(self):
        return self.answer


# -----------------------------CaptCha------------------------------------------------------#

class MakeImageCaptcha(models.Model):
    image_captcha = models.ImageField(null=True, blank=True, verbose_name='image captcha',
                                      upload_to='img_captcha')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image_captcha.name


class MakeAudioCaptcha(models.Model):
    audio_captcha = models.FileField(null=True, blank=True, verbose_name='audio captcha',
                                     upload_to='au_captcha')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.audio_captcha.name


# -----------------------------Custom_User---------------------------------------------------#

class ReUserManager(UserManager):

    def core_create_user(self, email, username, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        # user.password = make_password(password)  from django.contrib.auth.hashers import make_password
        user.save(using=self._db)
        return user

    def create_user(self, email, username=None, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_admin', False)

        return self.core_create_user(email=email, username=username, password=password, **extra_fields)

    def create_superuser(self, email, username=None, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', True)  # user.is_staff = True
        extra_fields.setdefault('is_superuser', True)  # user.is_superuser = True
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.core_create_user(email=email, username=username, password=password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True, unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    gender = models.CharField(max_length=35, blank=True, null=True)

    # groups = models.ManyToManyField(
    #     Group,
    #     verbose_name=_('groups'),
    #     blank=True,
    #     help_text=_(
    #         'The groups this user belongs to. A user will get all permissions '
    #         'granted to each of their groups.'
    #     ),
    #     related_name="user_set",
    #     related_query_name="user",
    # )
    #
    # user_permissions = models.ManyToManyField(
    #     Permission,
    #     verbose_name=_('user permissions'),
    #     blank=True,
    #     help_text=_('Specific permissions for this user.'),
    #     related_name="user_set",
    #     related_query_name="user",
    # )

    objects = ReUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('User')
        # abstract = True

    def __str__(self):
        return self.username + "-" + self.email

    # def has_perm(self,perm,object=None):
    #     return self.is_admin
    #
    # def has_module_perms(self, app_label):
    #     return True
