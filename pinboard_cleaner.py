#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1"
__author__ = "Arne Jokela"
__copyright__ = "Copyright 2016, Arne Jokela"
__maintainer__ = "@jokela"
__email__ = "arne@jokela.co"
__license__ = "Unlicense"

import secret

import argparse
import logging
import ssl
import sys

from bs4 import BeautifulSoup
import pinboard
import requests

TAG_TO_ADD = '.n'

pb = pinboard.Pinboard(secret.token)

def get_html(b):
    try:
        request = requests.get(b.url)
        request.raise_for_status()
        return BeautifulSoup(request.text, 'html.parser')
    except Exception as e:
        try:
            logging.debug('Retrieving %s as a browser' % b.url)
            request = requests.get(b.url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            })
            request.raise_for_status()
            return BeautifulSoup(request.text, 'html.parser')
        except Exception as e:
            logging.error('%s: %s' % (b.url, e))
            return None

def update_title(b,p):
    if p.title:
        title = p.title.text.strip()
    else:
        title = b.description
    if title and (b.description != title):
        logging.debug('Updating title for %s' % b.url)
        b.description = title if isinstance(title, str) else unicode(title, 'utf-8')
        return True
    else:
        return False

def update_extended(b,p):
    if p.find(attrs={'name':'description'}):
        try:
            description = p.find(attrs={'name':'description'})['content']
        except KeyError:
            description = None
    elif p.find(property=['twitter:description','og:description']):
        try:
            description = p.find(property=['twitter:description','og:description'])['content']
        except KeyError:
            description = None
    else:
        description = None

    if description and (b.extended != description):
        if len(description) > 255:
            description = description[:252] + '...'
        b.extended = description if isinstance(description, str) else unicode(description, 'utf-8')
        return True
    else:
        return False

def canonicalize_url(b,p):
    canonical = p.find(rel='canonical')

    try:
        # Some canonical urls are relative, why?
        if canonical and canonical['href'].startswith('http'):
            canonical_url = canonical['href']
        else:
            canonical_url = ''
    except KeyError:
        canonical_url = ''

    if canonical_url and (b.url != canonical_url):
        try:
            b.tags.append('.c')
            a = pb.posts.add(url=canonical_url, description=b.description.encode('utf-8'), extended=b.extended.encode('utf-8'), tags=b.tags, dt=b.time, replace='yes', shared=b.shared, toread=b.toread)
            if a:
                pb.posts.delete(url=b.url)
                logging.info('Replaced %s with %s' % (b.url, canonical_url))
            return True
        except Exception as e:
            logging.error("Couldn't replace %s with %s: %s" % (b.url, canonical_url, e))
            return False

def main():
    bookmarks = pb.posts.all(tag=args.tag_to_find, results=args.max_results)
    succeeded = 0
    failed = 0
    retitled = 0
    reextended = 0
    canonicalized = 0
    failures = ''

    logging.warning('Start: %d bookmarks to process' % len(bookmarks))

    for i, bookmark in enumerate(bookmarks):
        logging.info('Cleaning %d of %d: %s' % (i+1, len(bookmarks), bookmark.url))
        html = get_html(bookmark)
        if html:
            if update_title(bookmark,html):
                retitled += 1
            if update_extended(bookmark,html):
                reextended += 1
            bookmark.tags.remove(args.tag_to_find) if args.tag_to_find in bookmark.tags and args.tag_to_find != '.test' else bookmark.tags
            bookmark.tags.append(TAG_TO_ADD) if TAG_TO_ADD not in bookmark.tags else bookmark.tags
            try:
                params = {
                    'url': bookmark.url,
                    'description': bookmark.description.encode('utf-8'),
                    'extended': bookmark.extended.encode('utf-8'),
                    'tags': bookmark.tags,
                    'dt': bookmark.time,
                    'replace': 'yes',
                    'shared': bookmark.shared,
                    'toread': bookmark.toread,
                }
                pb.posts.add(**params)

                logging.info('Cleaned %s' % bookmark.url)
                succeeded += 1
            except Exception as e:
                logging.error('Save failed for %s with error %s' % (bookmark.url, e))
                failed += 1
                failures += bookmark.url + ' '
            if canonicalize_url(bookmark,html):
                canonicalized += 1
        else:
            logging.error('HTML not retrieved for %s' % bookmark.url)
            failed += 1
            failures += '\n' + bookmark.url

    logging.warning('Done: %d retitled, %d descriptions updated, %d canonicalized, %d succeeded, %d failures' % (retitled, reextended, canonicalized, succeeded, failed))
    if failures:
        logging.warning('Failures at %s' % failures)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log', dest='loglevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='set the logging level (default WARNING)', default='INFO')
    parser.add_argument('-m', '--max', dest='max_results', type=int, help='clean this many bookmarks (default 50)', default=50)
    parser.add_argument('-t', '--tag', dest='tag_to_find', help='clean bookmarks with this tag (default ".2n")', default='.2n')
    args = parser.parse_args()
    logging.basicConfig(filename='pinboard_cleaner.log', level=args.loglevel, format='%(levelname)s %(asctime)s %(message)s')
    main()
