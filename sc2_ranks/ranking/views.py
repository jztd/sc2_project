#django
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpRequest
from django.template import RequestContext

#from the project
from ranking.models import player, match, tournament

#trueskill crap
from trueskill import Rating, rate_1vs1, TrueSkill, expose
from trueskill.backends import cdf

#other stuff
from bs4 import BeautifulSoup
import re
import urllib2
from datetime import datetime, date
from math import sqrt
from decimal import Decimal

def get_country_race(name):
	try:
		url = urllib2.urlopen('http://wiki.teamliquid.net/starcraft2/'+name)
		soup = BeautifulSoup(url)
		table = soup.find_all('tr', valign='top')
		for each in table:
			if each.find('th') == None:
				continue
			else:
				if each.find('th').get_text().strip() == 'Race:':
					race = each.find('th').findNext('td').get_text()
				elif each.find('th').get_text().strip() == 'Country:':
					country = each.find('th').findNext('td').get_text()
		country_race_list = [country.strip(),race.strip()]
		return country_race_list
	except:
		pass



def Pwin(rA=Rating(), rB=Rating()):
    deltaMu = rA.mu - rB.mu
    rsss = sqrt(rA.sigma**2 + rB.sigma**2)
    return cdf(deltaMu/rsss)

def check_tournament_exists(tournament_name):
	tournament_object = tournament.objects.filter(name= tournament_name)
	if tournament_object.exists() == True:
		return True
	elif tournament_object.exists() == False:
		return False
def create_tournament(tournament_name, website):
	tournament_object = tournament(name=tournament_name, url=website)
	tournament_object.save()

def get_tournament_name(website, stage):
# stage is bracket or groupstage should be b or g
	page = urllib2.urlopen(website)
	soup = BeautifulSoup(page)
	raw_tourny_title = soup.title.get_text()

	full_tourny_title = raw_tourny_title.split('-')
	tourny_title = full_tourny_title[0].strip()
	if stage == 'b':
		tourny_title += ' Bracket'
	elif stage == 'g':
		pass
	else:
		raise Exception('Invalid value for "stage" accepted values are "b" and "g" ')
	return tourny_title


def check_players_exist(player_1_name, player_2_name):
	#get player objects
	player_one = player.objects.filter(name=unicode(player_1_name))
	player_two = player.objects.filter(name=unicode(player_2_name))
	# check if each one exists, if they don't make a new one
	if player_one.exists() == False:
		country_race = get_country_race(player_1_name)
		if country_race is not None:
			player_1 = player(name=player_1_name, mu=25, sigma = 8.333, country=country_race[0], race=country_race[1])
		else:
			player_1 = player(name=player_1_name, mu=25, sigma=8.333)
		player_1.save()
	if player_two.exists() == False:
		country_race = get_country_race(player_2_name)
		if country_race is not None:
			player_2 = player(name=player_2_name, mu=25, sigma= 8.333, country=country_race[0], race=country_race[1])
		else:
			player_2 = player(name=player_2_name, mu=25, sigma= 8.333)
		player_2.save()


def create_new_match(player_1, player_2, winner, date, tournament_name):
	# creates a new match with the players and winner
	tournament_object = tournament.objects.get(name=tournament_name)
	if winner == '':
		return ''
	player_one = player.objects.get(name=player_1)
	player_two = player.objects.get(name=player_2)
	if winner == player_1:
		new = match(winner = player_one, loser=player_two, tournament= tournament_object)
		new.save()
		new.players.add(player_one)
		new.players.add(player_two)
	elif winner == player_2:
		new = match(winner = player_two, loser = player_one, tournament= tournament_object)
		new.save()
		new.players.add(player_one)
		new.players.add(player_two)
	tournament_object.matches.add(new)
	new.date = date
	new.save()
	tournament_object.matches.add(new)
	tournament_object.save()

def update_wins(player_1, player_2, winner):
	# here we update the wins of the players in a match yaaay
	if winner == player_1:
		match_winner = player.objects.get(name=player_1)
		match_loser = player.objects.get(name=player_2)
		losses = match_loser.losses
		wins = match_winner.wins
		num = wins+1
		new_losses = losses+1
		match_loser.losses = new_losses
		match_winner.wins = num
		match_loser.save()
		match_winner.save()
	elif winner == player_2:
		match_winner = player.objects.get(name=player_2)
		match_loser = player.objects.get(name=player_1)
		losses = match_loser.losses
		wins = match_winner.wins
		num = wins+1
		new_losses = losses+1
		match_loser.losses = new_losses
		match_winner.wins = num
		match_loser.save()
		match_winner.save()

def update_rating(player_1, player_2, winner):
	# now let's to some complicated math...just kidding trueskill will do it for us
	player_one = player.objects.get(name=player_1)
	player_two = player.objects.get(name=player_2)
	player_1_mu =  player_one.mu
	player_1_sigma = player_one.sigma
	player_2_mu = player_two.mu
	player_2_sigma =  player_two.sigma
	# okay we got all of the variables because Django is fucking stupid
	# now we get to recalculate the rating based on who the fuck won
	player_1_current_rating = Rating(float(player_1_mu), float(player_1_sigma))
	player_2_current_rating = Rating(float(player_2_mu), float(player_2_sigma))
	# we got ourselves some ratings here let's give them a match
	if winner == player_1:
		player_1_new_rating, player_2_new_rating = rate_1vs1(player_1_current_rating, player_2_current_rating)
	elif winner == player_2:
		player_2_new_rating, player_1_new_rating = rate_1vs1(player_2_current_rating, player_1_current_rating)
	player_one.mu = player_1_new_rating.mu
	player_one.sigma = player_1_new_rating.sigma
	player_two.mu = player_2_new_rating.mu
	player_two.sigma = player_2_new_rating.sigma
	player_one.save()
	player_two.save()


def save_matches(request):
	#open the url we want to scrape
	url = urllib2.urlopen("http://www.sc2ratings.com")
	#make soupe of it
	soup = BeautifulSoup(url)
	#find the most recent match's container which is the first set displayed on the site
	recent_matches = soup.find('div', class_="season-round-date-container")
	#find all of the div's that contain individual matches within the most recent set of matches
	data = recent_matches.find_all('div', id=re.compile('match-id-'))
	for each in data:
		try:
			#find both of the players in the match
			players = each.find_all('a', class_="player-link")
			#save the players in the order they were found
			player_1 = players[0].get_text()
			player_2 = players[1].get_text()
			# find the winner 
			winner = each.find('div', class_='winner').get_text()
			winner = winner.replace(' ','')
			# making the players and the new match
			check_players_exist(player_1, player_2)
			create_new_match(player_1, player_2, winner)
			update_wins(player_1, player_2, winner)
			update_rating(player_1, player_2, winner)
		except:
			continue
	return HttpResponse('OK')
def display(request):
	#this is the main view
	#it's going to get all of our awesome players from the database
	#and create a leaderboard time thing from them based on their 
	#ratings...it sounds stupid simple but it will probably be harder than anything else here
	all_players = player.objects.all()
	player_list = {}
	final_list = []
	player_skills = []
	player_rounded_skills = []
	for each in all_players:
		if each.wins + each.losses > 5:
			player_mu = each.mu
			player_sigma = each.sigma
			player_rating = Decimal(expose(Rating(float(player_mu), float(player_sigma))))
			#if player_rating in player_list:
			#	player_rating += Decimal(.000000000000000000000000001)
			player_list[player_rating] = each
	sorted_player_list = sorted(player_list, reverse=True)
	for each in sorted_player_list:
		final_list.append(player_list[each])
		player_skills.append(each)
	index_list = range(1, len(all_players)+1)
	for each in player_skills:
		player_rounded_skills.append(round(each, 1))
	zipped_list = zip(final_list, player_rounded_skills, index_list)
	return render(request, 'display.html', {'player_list': final_list, 'skill_list': player_skills, 'zipped_list':zipped_list, 'index_list': index_list, })

def scrape_liquid_groupstages(request, url):
	# ok this should work for all of liquipedia's group stage pages...in theory
	page = urllib2.urlopen(url)
	soup = BeautifulSoup(page)
	#this is a group stage page so we need to get all of the tables that are going to have our matches in it
	#check if the tournament has already been recorded
	tournment_name = get_tournament_name(url,'g')
	tournament_exists = check_tournament_exists(tournment_name)
	if  tournament_exists == True:
		return HttpResponse('Tournament Already Exists')
	else:
		create_tournament(tournment_name, url)
	div_boxes = soup.find_all('div', attrs={'style':'display:inline-block; vertical-align: top; margin: 0 0 0 0;padding-right:4em;'})
	for div in div_boxes:
		tables_of_matches = div.find_all('table', class_= "wikitable collapsible collapsed")
		try:
			match_date = div.find_all('td', attrs={'style':'background-color:#f2f2f2; font-size:85%; line-height:90%; height:13px; text-align:center;'})[0].get_text()
			new_date, time = match_date.split('-')
			new_date = new_date.strip()
			new_date = new_date.replace(',', '')
			date_object = datetime.strptime(new_date, '%B %d %Y')
		except :
			date_object = date.today()
		#then iterate over them
		for table in tables_of_matches:
			#in each table that we found before we are going to find all of the rows (the first one is a blank row so ....keep that in mind)
			body = table.find_all('tr', style_="")
			#for each row we are going to get all of that good good data
			for each in body:
				try:
					# This gets a little confusing but basically...fuck team liquid :D
					# The important part is that the first time through you hit an empty row
					# so you have to except the error..... it will probably bite me later
					players = each.find_all('td', width='44%')
					scores = each.find_all('td', width='6%')
					winners = [scores[0].get_text(), scores[1].get_text()]
					# if a person withdrew we don't want that data so break the loop
					if winners[0].strip().upper() == 'W' or winners[1].strip().upper() == 'W':
						continue
					if int(scores[0].get_text()) > int(scores[1].get_text()):
						winner = players[0].get_text()
					else:
						winner = players[1].get_text()
					player_1 = players[0].get_text()
					player_1 = player_1.strip()
					player_2 = players[1].get_text()
					player_2 = player_2.strip()
					winner = winner.strip()
					check_players_exist(player_1, player_2)
					create_new_match(player_1, player_2, winner, date_object, tournament.objects.get(name=tournment_name))
					update_wins(player_1, player_2, winner)
					update_rating(player_1, player_2, winner)
				except IndexError:
					continue
	return HttpResponse('OK')
def scrape_liquid_brackets(request, url):
	page = urllib2.urlopen(url)
	soup = BeautifulSoup(page)
	bracket = soup.find_all('div', class_='bracket-column', style="width:150px")
	tournament_name = get_tournament_name(url,'b')
	tournament_exists = check_tournament_exists(tournament_name)
	if  tournament_exists == True:
		return HttpResponse('Tournament Already Exists')
	else:
		create_tournament(tournament_name, url)
	for column in bracket:
		try:
			matches = column.find_all('div', class_="bracket-game")
			match_date = column.find_all('div', attrs={'style':'border-bottom: 1px dotted #aaa; padding:2px; font-size:85%; line-height:12.5px; text-align:center;'})[0].get_text()
			new_date, time = match_date.split('-')
			new_date = new_date.strip()
			new_date = new_date.replace(',','')
			date_object = datetime.strptime(new_date, '%B %d %Y')
		except:
			date_object = date.today()
		for match in matches:
			try:
				player_1 = match.find('div', class_="bracket-player-top").get_text()
				player_2 = match.find('div', class_="bracket-player-bottom").get_text()
				player_1 = player_1.strip()
				player_2 = player_2.strip()
				# for some reason match score is in the same field as the player name so we have to get it out mmkay?
				player_1 = player_1[0:len(player_1)-1]
				player_2 = player_2[0:len(player_2)-1]
				scores = match.find_all('div', class_="bracket-score")
				player_1_score = scores[0].get_text()
				player_2_score = scores[1].get_text()
				player_1 = player_1.strip()
				player_2 = player_2.strip()
				if int(player_1_score) > int(player_2_score):
					winner = player_1
				elif int(player_2_score) > int(player_1_score):
					winner = player_2
				else:
					continue
				check_players_exist(player_1, player_2)
				create_new_match(player_1, player_2, winner, date_object, tournament.objects.get(name=tournament_name))
				update_wins(player_1, player_2, winner)
				update_rating(player_1, player_2, winner)
			except:
				continue
	return HttpResponse('OK')

def display_player(request, given_player):
	player_name = player.objects.get(name=given_player)
	matches = match.objects.filter(players__name=player_name.name)
	player_rating = expose(Rating(float(player_name.mu), float(player_name.sigma)))
	return render(request,'player_display.html',{'matches':matches, 'player':player_name, 'rating': player_rating})

def display_match(request, match_id):
	match_object = match.objects.get(id=match_id)
	return render(request, 'display_match.html', {'match':match_object})
def display_tournament(request):
	all_tournaments = tournament.objects.all()
	return render(request, 'display_tournaments.html',{'tournament_list':all_tournaments})

def player_comparison(request):
	if request.is_ajax():
		p1 = request.GET['p1']
		p2 = request.GET['p2']
		try:
			p1_object = player.objects.get(name__iexact=p1)
		except:
			return render_to_response('percent.html', {'success':False, 'player': p1}, context_instance=RequestContext(request))
		try:
			p2_object = player.objects.get(name__iexact=p2)
		except:
			return render_to_response('percent.html', {'success':False, 'player': p2}, context_instance=RequestContext(request))
		p1_mu = p1_object.mu
		p1_sigma = p1_object.sigma
		p2_mu = p2_object.mu
		p2_sigma = p2_object.sigma
		win_percent = Pwin(Rating(float(p1_mu),float(p1_sigma)), Rating(float(p2_mu), float(p2_sigma)))
		win_percent = round((win_percent*100), 2)
		return render_to_response('percent.html', {'success':True, 'percent': win_percent, 'p1': p1_object, 'p2':p2_object} ,context_instance=RequestContext(request))
	else:
		return render(request, 'player_comparison.html', {})
def recalc_ratings(request):
	#this is going to recalculate ratings based on matches still in the system...hold onto your butts
	#please if anyone has a better idea let me know...this is probably the most in efficient way to do this
	all_tournaments = tournament.objects.all()
	all_players = player.objects.all()
	# reset every fucking player
	for each in all_players:
		each.mu = 25
		each.sigma = 8.333
		each.wins = 0
		each.losses = 0
		each.save()
	for tournament_ in all_tournaments:
		matches = match.objects.filter(tournament__name = tournament_)
		for match_ in matches:
			player_1 = match_.winner
			player_2 = match_.loser
			update_rating(player_1, player_2, player_1)
			update_wins(player_1, player_2, player_1)
	return HttpResponse('....It Worked...I Hope')
def manage(request):
	return render(request, 'tournament_add.html')






# Create your views here.
