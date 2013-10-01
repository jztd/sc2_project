from django.db import models
from datetime import date

class player(models.Model):
	name = models.CharField(max_length= 100, blank=False)
	race = models.CharField(max_length = 50, blank=True, default='Unknown')
	country = models.CharField(max_length = 50, default='Unknown')
	#jesus this was stupid...so all the data that trueskill needs has to be saved
	sigma = models.DecimalField(decimal_places = 4, max_digits = 10)
	mu = models.DecimalField(decimal_places = 4, max_digits = 10)
	rank = models.CharField(max_length= 100) # still not sure if this is a good idea or not
	wins = models.IntegerField(default = 0)
	losses = models.IntegerField(default = 0)

	def __unicode__(self):
		return self.name
	class Meta:
		ordering = ['name']
	

class match(models.Model):
	players = models.ManyToManyField('player', related_name ='players')
	date = models.DateField(default= date.today()) # still defaults to today if it can't find a date.....which will confuse the shit out of people
	winner = models.ForeignKey('player', related_name='winner')
	loser = models.ForeignKey('player', related_name='loser')
	tournament = models.ForeignKey('tournament', related_name='tournament')


class tournament(models.Model):
	name = models.CharField(max_length= 500, blank=False)
	url = models.URLField(max_length = 500)
	matches = models.ManyToManyField('match', related_name='tournament_matches')

	def __unicode__(self):
		return self.name
	class Meta:
		ordering = ['name']
	#def __unicode__(self):
	#	return self.players[0]
