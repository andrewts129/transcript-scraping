import requests
import os
from bs4 import BeautifulSoup

# If you want to configure this script to scrape the speeches of somebody other than Donald Trump, the variables
# 'tagPageUrl' and 'name' will need to be modified to fit your intended person

# This should point to the first page that lists all the articles with the tag of the person you want to get the
# speeches of
tagPageUrl = 'http://www.whatthefolly.com/tag/donald-trump/'

# This should be the name that WhatTheFolly uses right after the word "Transcript:" in the
# titles of their speech transcripts. For some politicians, multiple name/title combinations are used. For example, they
# refer to  Bernie Sanders as "Vermont Sen. Bernie Sander's", "Sen. Bernie Sanders", and "Bernie Sanders". When multiple
# beginnings are used, put them all in a list of strings.
names = ['Donald Trump']

# This is the name of the folder that the speech transcripts will be put in
folder = names[0] + ' Speeches'

# Create the folder if it does not exist in the running directory
if not os.path.exists(folder):
    os.mkdir(folder)

# Retrieves the page with tag results and sets it up to be scraped
tagPage = requests.get(url=tagPageUrl)
tagPageSoup = BeautifulSoup(tagPage.content, 'lxml')

# Gets the total number of pages that are shown at the bottom of the results so the script knows how many pages of
# results it needs to look at
pageNumbers = []
for pageNumber in tagPageSoup.select('a.page-numbers'):
    text = pageNumber.get_text()
    if text.isdigit():
        pageNumbers.append(int(text))

# This is the total number of pages
maxPage = max(pageNumbers)

# This will contain the title of every article scraped, with the 'Part x' part filtered out. This is used to account for
# speeches that WhatTheFolly gave the same title. More below.
articlesScraped = []

# This file will contain every speech that this script scrapes, without any kind of separation between separate
# speeches. If you're looking to do something with sentence analysis or Markov chains, this is probably the one you're
# interested in
bigFile = open(folder + '/AllSpeeches.txt', 'a')

# Gets a list of every number between 1 and the max page number, which is every page of results that needs to be scraped
pagesToScrape = list(range(1, maxPage + 1))

# Reverse it so that the oldest speeches come first
pagesToScrape.reverse()

for number in pagesToScrape:
    # This is the url of the page of results of articles, will go through every page as the loop progresses
    url = tagPageUrl + 'page/' + str(number) + '/'

    # Retrieves the page of results and sets it up for scraping
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'lxml')

    # Gets all of the article title links on the results page. Reverse them so that the oldest ones are scraped first.
    links = soup.select('h2.headline.smaller a')
    links.reverse()

    for link in links:
        # Gets the title of each article on the results page
        linkText = link.get_text()

        # If multiple name/title combinations are used in WhatTheFolly article titles, this checks for all of them
        for name in names:

            # Checks if an article is a speech transcript by looking to see if the article title follows the standard
            # WhatTheFolly convention of "Transcript: President Barack Obama's remarks/speech/whatever on....
            if 'Transcript: ' + name in linkText:

                # If it is a transcript, get the url that the link leads to and set it up for scraping
                articleUrl = link.get('href')
                print('URL to scrape: ' + articleUrl)
                ArticlePage = requests.get(articleUrl)
                ArticleSoup = BeautifulSoup(ArticlePage.content, 'lxml')

                # This retrieves the text content of the speech. However, this also includes the context of the speech
                # inserted by the WTF editors and links to other parts of the speech. Those need to be filtered out
                article = ArticleSoup.select('div.article p')

                # Processes the text in the article line by line
                lines = []

                for line in article:
                    # The context inserted by the editors have the '(b)old' or 'strong' tag. Links (to other parts of
                    # the speech) have the 'a' tag. If any of those tags are found, don't add their text to the speech
                    # text output
                    if not line.find('strong') and not line.find('b') and not line.find('a'):
                        text = line.get_text()

                        # '###' is used to indicate that the speech is finished, and '…' is used to indicate that the
                        # speech will continued in another article. If either one of these is found, that means there is
                        #  no more relevant text on the page and should move onto the next article
                        if text == '###' or text == '…':
                            break
                        else:
                            # Adds the line processed to a list that will later be written to a text file
                            text = text.strip()
                            lines.append(text)

                # These next few lines make the title look the same for every part of a speech so that they are all
                # outputted to the same text file
                title = ArticleSoup.select('h1.headline')[0].get_text()
                title = title.replace('Transcript: ', '')
                if '– Part' in title:
                    indexOfPart = title.index('– Part')
                    title = title[:indexOfPart]
                title = title.strip()

                # There are a few speeches that are given the same article title because they were given by the same
                # person at the same place. This throws a number at the end if a speech with the same title has been
                # processed so that it doesn't get placed into the same text file as the older speech.
                # If the speech with the same title is the last one processed, that probably means that it's another
                # part of the same speech and doesn't need to be separated
                if title in articlesScraped and articlesScraped[-1] != title:
                    title += str(articlesScraped.count(title) + 1)

                # This is the file that the individual speech will be placed in. You're probably going to have a lot of
                # these files
                file = open(folder + '/' + title + '.txt', 'a')

                # Writes every line of the speech into both the individual speech file and the one containing every
                # speech given by the person
                for line in lines:
                    file.write(line + '\n')
                    bigFile.write(line + '\n')

                file.close()

                # Creates a list of every article scraped so that speeches with the same name can be accounted for and
                # not written into the same text file
                articlesScraped.append(title)
                print('Scraped ' + title)

bigFile.close()
