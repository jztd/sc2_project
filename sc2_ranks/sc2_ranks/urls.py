from django.conf.urls import patterns, include, url
import ranking.views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'ranking.views.display', name='home'),
    url(r'^save_matches', 'ranking.views.save_matches'),
    url(r'^scrape_liquid_groupstages/(?P<url>.{0,500})/$', 'ranking.views.scrape_liquid_groupstages'),
    url(r'^scrape_liquid_brackets/(?P<url>.{0,500})/$', 'ranking.views.scrape_liquid_brackets'),
    #url(r'^tournaments/$', 'ranking.views.tournaments'),
    url(r'^player/(?P<given_player>.{0,500})/$', 'ranking.views.display_player', name='display_player'),
    url(r'^match/(?P<match_id>.{0,15})/$', 'ranking.views.display_match', name='display_match'),
    url(r'^tournaments', 'ranking.views.display_tournament' ,  name='display_tournaments'),
    url(r'^player_comparison' , 'ranking.views.player_comparison', name='player_comparison'),
    url(r'^manage', 'ranking.views.manage', name='manage'),
    url(r'^update_this_shit', 'ranking.views.recalc_ratings', name='recalc_ratings'),
    #url(r'^compare', 'ranking.views.calc_percent_win' ,name='calc_percent_win'),
    #url(r'^sc2_ranks/', include('sc2_ranks.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
