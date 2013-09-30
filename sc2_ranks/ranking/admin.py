from django.contrib import admin
from ranking.models import player, match, tournament


admin.site.register(player)
admin.site.register(match)
admin.site.register(tournament)