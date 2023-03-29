from django.contrib import admin

from users.models import User, UserSubscription

admin.site.register(UserSubscription)


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


admin.site.register(User, UserAdmin)
