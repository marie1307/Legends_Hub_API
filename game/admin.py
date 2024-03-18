from django.contrib import admin
from game.models import CustomUser, Team, Notification, Invitation

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Team)
admin.site.register(Invitation)
admin.site.register(Notification)
