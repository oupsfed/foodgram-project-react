from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models import UserSubscription

admin.site.register(UserSubscription)

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'first_name',
        'last_name',
        'email',
        'username',
    )
    list_filter = ('email', 'username')
    list_display_links = ('username',)
    empty_value_display = '-пусто-'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
