import django
import sys, os
import csv

sys.path.append('/home/galm/software/django/tmv/BasicBrowser/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BasicBrowser.settings")
django.setup()

import twitter.models as tm
import tweepy
from parliament.models import *

from django.db.models import Count
from django.db.models.fields import DateField
from django.db.models.functions import Cast
from django.conf import settings

auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_SECRET)
api = tweepy.API(auth,wait_on_rate_limit=True)

parl = Parl.objects.get(country_id=2921044,level='N')
# persons = Person.objects.filter(
#     utterance__document__parlperiod__parliament=parl
# ).distinct()

persons = Person.objects.filter(
    seat__parlperiod__parliament=parl
).distinct()

with open('MdB_twitter_handle_list.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sc = row['handle'].replace('@','')
        try:
            tuser = tm.User.objects.get(screen_name=sc)
            tuser.monitoring=True
            tuser.save()
        except:
            try:
                u = api.get_user(screen_name=sc)
                udata = u._json
                try:
                    tuser = tm.User.objects.get(
                        id = udata['id']
                    )
                except:
                    tuser, created = tm.User.objects.get_or_create(
                        id = udata['id'],
                        screen_name = udata['screen_name']
                    )
                    print(f"created user {tuser}")
            except:
                continue
                print(f"couldn't find user {sc}")
        ## find mdb
        if row['name'] == "Dagmar Schmidt":
            tuser.person = Person.objects.get(pk=62666)
            tuser.save()
            continue

        sname = row['name'].split()[-1]
        fname = row['name'].split()[0]
        if "eue" not in sname and "oue" not in sname and "aue" not in sname:
            sname = sname.replace("ue","ü")
        smatches = persons.filter(surname__icontains=sname)
        n_matches=0
        matches = []
        for sm in smatches:
            if sm.first_name.lower() in str(tuser).lower():
                n_matches+=1
                matches.append(sm)
        if n_matches == 0:
            for sm in smatches:
                if str(tuser).lower().split()[0] in sm.first_name.lower():
                    n_matches+=1
                    matches.append(sm)
                elif fname.lower() in sm.first_name.lower():
                    n_matches+=1
                    matches.append(sm)

        if n_matches > 1:
            smatches = persons.filter(surname__iexact=sname)
            n_matches=0
            matches = []
            for sm in smatches:
                if fname.lower() == sm.first_name.lower():
                    n_matches+=1
                    matches.append(sm)

        if n_matches > 1:
            print('\n####\n#### MULTIPLE MATCHES!')
            for sm in matches:
                print(f"{tuser} matches {sm}")
        elif n_matches == 0 :
            if smatches.count()==1:
                pass #match
            else:
                print("\n####\n#### No match for")
                print(tuser)
                print(sname)
        else:
            tuser.person = matches[0]
            tuser.save()


        #if smatches.count()==1:
        #    print(f"{tuser} matches {smatches.first()}")
