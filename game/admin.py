from django.contrib import admin
from game.models import CustomUser, Team, Notification, Invitation, Tournament, TournamentRegistration, GameSchedule, Game

admin.site.register(CustomUser)
admin.site.register(Team)
admin.site.register(Invitation)
admin.site.register(Notification)
admin.site.register(Tournament)
admin.site.register(TournamentRegistration)
admin.site.register(GameSchedule)
# admin.site.register(Game)
