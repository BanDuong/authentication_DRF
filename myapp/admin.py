from django.contrib import admin
from .models import Questions,Answers,User
# Register your models here.

admin.site.register(Questions)
admin.site.register(Answers)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id","username","first_name","last_name","email","is_staff","is_active","is_admin","is_superuser")
    list_filter = ("id","username","first_name","last_name","email","is_staff","is_active","is_admin","is_superuser")
    search_fields = ("id","username","email")

