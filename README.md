# pinboard_cleaner
_A python script that cleans up Pinboard bookmarks_

I use various browsers and devices to read the internets, and various Pinboard extensions and plugins to add bookmarks to the pinboard.in service. These currently include:
* Bookmarks for Chrome and Safari
* Pinner and Pushpin for iOS
* Reeder's service button

This leads to a few annoying inconsistencies in my collection's metadata, for example:
* Titles are drawn from different mysterious sources, generally the `<title>` tag but sometimes `<h1>` or something else. My preference is for it to be the content of the `<title>`.
* Extended text is either left to manual entry or automatically pulled from wherever. My preference is for it to be the content of the publisher's HTML description.
* URL is whatever is presented to the client, including mobile-specific hostnames (e.g. mobile.nytimes.com or en.m.wikipedia.org) or redirect services (e.g. feedproxy.google.com or feeds.gawker.com). My preference is to use the publisher's canonical URL.

pinboard\_cleaner goes through your Pinboard bookmarks and compares them to the source HTML, replacing existing data with my preferences as described above.

You'll need a file called "secret.py" in the same directory as the script. The secret.py file should contain a single line with your token in the form

`token = 'username:TOKENSTRING'`

Running `python pinboard_cleaner.py` on the command line will search for your first 50 bookmarks tagged ".2n", clean them up, and change the tag to ".n".
Running `python pinboard_cleaner.py --help` will tell you how to switch things up.

Makes use of:
* Dan Loewenherz's Pinboard.py ([https://pypi.python.org/pypi/pinboard])
* Kenneth Reitz's Requests ([http://www.python-requests.org/en/master/])
* Leonard Richardson's BeautifulSoup ([https://www.crummy.com/software/BeautifulSoup/])
