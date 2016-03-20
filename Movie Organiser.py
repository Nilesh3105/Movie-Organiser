import sqlite3
import urllib
import json
import re
import os
key = None # Google Search API key
cx = None  # Google Custom Search Engine ID
conn = sqlite3.connect('movies.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS movie(title TEXT, year INT, plot TEXT, imdbrating REAL, genre TEXT, rated TEXT, path TEXT)')

patters_to_strip = [
    '((19|20)\d{2})',
    '\[.*\]',
    '\(.*\)',
    '{.*}',
    'dvd\.?rip',
    'xvid',
    'CD\d+',
    'axxo|YIFY|Ganool|UsaBitcom|ExtraTorrentRG|DiAMOND|ARCHiViST|HELLRAZ0R|GlowGaze|BOKUTOX|anoXmous|GAZ|Ozlem',
    'mp3|aac',
    'hdtv',
    'divx',
    '\d{0,2}fps',
    '\d{0,4}kbps',
    'hddvd',
    '(x[ ]?)?264',
    'torr?ent.',
    'extended|UNRATED|Anniversary Edition|remastered',
    '\d+[MG]B',
    '\d{3,4}p',
    'Part\d',
    '-',
    'Blue?Ray',
    '(Br)?Rip',
    ]
    
file_types = ['avi', 'mp4', 'mkv', 'VOB', 'm4v', 'flv', '3gp']

def data(title, year, plot, imr, gen, rate, path):
    c.execute("SELECT * FROM movie WHERE title =? AND year = ?", (title, year))
    if not c.fetchall():
        c.execute("INSERT INTO movie VALUES(?, ?, ?, ?, ?, ?, ?)", (title, year, plot, imr, gen, rate, path))
        conn.commit()
        return True
  
def print_row(row):
    print "Title: ", row[0]
    print "Release Year:", row[1]
    print "Plot:", row[2]
    print "IMDB rating: ", row[3]
    print "Genre: ", row[4]
    print "Rated: ", row[5]
    print "Path: ", row[6]
    print "\n"

def search():
    title=raw_input("Title: ").strip()
    genre_list=raw_input("Genre: ").split()
    min_rating=raw_input("Minimum IMDBRating: ")
    max_rating=raw_input("Maximum IMDBRating: ")
    min_year=raw_input("Min year: ")
    max_year=raw_input("Max year: ")
    
    if not genre_list:
        genre_list.append("")
    if min_rating:
        min_rating = float(min_rating)
    else:
        min_rating = 0.0
    if max_rating:
        max_rating = float(min_rating)
    else:
        max_rating = 10.0
    if min_year:
        min_year = int(min_year)
    else:
        min_year = 1900
    if max_year:
        max_year = int(max_year)
    else:
        max_year = 2100
    for genre in genre_list:
        c.execute("SELECT * FROM movie WHERE title LIKE ? AND imdbrating >=? AND imdbrating <= ? AND year >= ? AND year <= ? AND genre LIKE ? ORDER BY imdbrating DESC",
                  ("%"+title+"%", min_rating, max_rating, min_year, max_year, "%"+genre+"%"))
        movie_list = c.fetchall()
        print "\nFound", len(movie_list),"results\n"
        for row in movie_list:
           print_row(row)
        
def is_movie(filename):
    f_type = filename.split('.')[-1]
    if f_type in file_types:
        return True
    else:
        return False

def get_movie_name(filename):
    end = filename.rfind('.')
    movie_name = filename[0:end]
    try:
        mo = re.search('((19|20)\d{2})',movie_name)
        year = None
        if mo:
            year = int(mo.group())
    except:
            year = None
    movie_name = movie_name.replace('.', ' ')
    movie_name = strip_patterns(movie_name)
    movie_name = movie_name.strip()
    return movie_name,year

def strip_patterns(movie_name):
    for p in patters_to_strip:
        regex = re.compile(p, re.IGNORECASE)
        movie_name = regex.sub("", movie_name)
    return movie_name

def google_movie_title(movie_name):
    url = "https://www.googleapis.com/customsearch/v1?"
    url = url + urllib.urlencode({"q":movie_name, "key":key, "cx":cx})
    data = urllib.urlopen(url).read()
    js = json.loads(data)
    if "items" in js:
        try:
            id = js["items"][0]["pagemap"]["metatags"][0]["pageid"]
        except:
            id = None
        return id

def movie_data(movie_name,year=None):
    serviceurl = "http://www.omdbapi.com/?"
    if len(movie_name) < 1:
        return None
    url = serviceurl + urllib.urlencode({'t':movie_name, 'y':year})
    try:
        data = urllib.urlopen(url).read()
    except:
        print "Check your internet connection"
        return None
    js = json.loads(data)
    if js["Response"] != "True" and key and cx:
        movie_title = google_movie_title(movie_name)
        url = serviceurl + urllib.urlencode({'i':movie_title, 'y':year})
        data = urllib.urlopen(url).read()
        js = json.loads(data)
        
    if js["Response"] == "True":
        for x in js:
            js[x] = js[x].encode('ascii','ignore')
        try: js["imdbRating"] = float(js["imdbRating"])
        except ValueError:
            pass
        return js
        

def movies_in_path(path):
    if(os.path.exists(path)):
        for (path, subdirs, files) in os.walk(path):
            for filename in files:
                if is_movie(filename) == True:
                    movie_name,year = get_movie_name(filename)
                    js = movie_data(movie_name, year)
                    if js:
                        js["Path"] = os.path.join(path,filename)
                        if data(js["Title"], js["Year"], js["Plot"], js["imdbRating"], js["Genre"], js["Rated"], js["Path"]):
                            print "Title:",js["Title"]
                            print "Year:",js["Year"]
                            print "Plot:",js["Plot"]
                            print "imdbRating:",js["imdbRating"]
                            print "Genre:",js["Genre"]
                            print "Rated:", js["Rated"]
                            print "Path:", js["Path"]
                            print "\n"

while True:
    print """
    1. Update Database
    2. Search Database
    0. Exit
    """
    choice= raw_input("Enter Choice: ")
    if choice == "1":
        path = raw_input("Enter path: ")
        movie_list = movies_in_path(path)
    elif choice == "2":
        search()
    elif choice == '0':
        c.close()
        conn.close()
        break
    else:
        print "Invalid Choice"
