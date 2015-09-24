"OrderPortal: Search page."

from __future__ import print_function, absolute_import

import logging
import pprint
import urlparse

import couchdb
import tornado.web

from . import constants
from . import saver
from . import settings
from . import utils
from .fields import Fields
from .requesthandler import RequestHandler


class Search(RequestHandler):
    "Search. Currently only orders and staff."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        orig = self.get_argument('term', '')
        params = dict(term=orig)
        items = []
        # Keep this in sync with JS script 'designs/order/views/keyword.js'
        term = orig.replace(':', ' ')
        term = term.replace(',', ' ')
        term = term.replace("'", ' ')
        term = term.strip()
        parts = [part for part in term.split() if part]
        # Search order titles
        view = self.db.view('order/keyword')
        id_sets = []
        for part in parts:
            id_sets.append(set([r.id for r in
                                view[part : part+constants.HIGH_CHAR]]))
        if id_sets:
            # All words must exist in title
            id_set = reduce(lambda i,j: i.intersection(j), id_sets)
            items.extend([self.get_entity(id, doctype=constants.ORDER)
                          for id in id_set])
        # Search account last names
        view = self.db.view('account/last_name')
        id_sets = []
        for part in parts:
            id_sets.append(set([r.id for r in
                                view[part : part+constants.HIGH_CHAR]]))
        # Only require one hit in last name
        if id_sets:
            id_set = reduce(lambda i,j: i.union(j), id_sets)
            items.extend([self.get_entity(id, doctype=constants.ACCOUNT)
                          for id in id_set])
        # Search account first names
        view = self.db.view('account/first_name')
        id_sets = []
        for part in parts:
            id_sets.append(set([r.id for r in
                                view[part : part+constants.HIGH_CHAR]]))
        # Only require one hit in first name
        if id_sets:
            id_set = reduce(lambda i,j: i.union(j), id_sets)
            items.extend([self.get_entity(id, doctype=constants.ACCOUNT)
                          for id in id_set])
        # Search dynamically defined indexes for order fields
        try:
            fields = self.db['_design/fields']['views'].keys()
        except (couchdb.ResourceNotFound, KeyError):
            fields = []
        for field in fields:
            view = self.db.view("fields/{}".format(field))
            id_sets = []
            for part in parts:
                id_sets.append(set([r.id for r in
                                    view[part : part+constants.HIGH_CHAR]]))
            if id_sets:
                id_set = reduce(lambda i,j: i.intersection(j), id_sets)
                items.extend([self.get_entity(id, doctype=constants.ORDER)
                              for id in id_set])
        # All items contain 'modified'
        items.sort(lambda i,j: cmp(i['modified'], j['modified']), reverse=True)
        # Page
        page_size = self.current_user.get('page_size') or constants.DEFAULT_PAGE_SIZE
        count = len(items)
        max_page = (count - 1) / page_size
        try:
            page = int(self.get_argument('page', 0))
            page = max(0, min(page, max_page))
        except (ValueError, TypeError):
            page = 0
        start = page * page_size
        end = min(start + page_size, count)
        items = items[start : end]
        params['page'] = page
        self.render('search.html',
                    items=items,
                    params=params,
                    start=start+1,
                    end=end,
                    max_page=max_page,
                    count=count)


class SearchFields(RequestHandler):
    "Define which fields to index for search. Rewrites a design document."

    MAP_TEMPLATE = """function(doc) {{
  if (doc.orderportal_doctype !== 'order') return;
  if (!doc.fields.{fieldid}) return;
  var cleaned = doc.fields.{fieldid}.replace(/[:,']/g, " ");
  var words = cleaned.split(/\s+/);
  words.forEach(function(word) {{
    if (word.length > 2 && !lint[word]) emit(word, null);
  }});
}};
var lint = {{'and': 1, 'the': 1, 'was': 1, 'not': 1}};"""

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        try:
            doc = self.db['_design/fields']
        except couchdb.ResourceNotFound:
            doc = dict()
        self.render('search_fields.html', views=doc.get('views'))

    @tornado.web.authenticated
    def post(self):
        self.check_admin()
        try:
            doc = self.db['_design/fields']
        except couchdb.ResourceNotFound:
            doc = dict(_id='_design/fields')
        views = doc.setdefault('views', dict())
        for delete_field in self.get_arguments('delete_field'):
            try:
                views.pop(delete_field)
            except KeyError:
                logging.debug("no such field %s", delete_field)
        for add_field in self.get_argument('add_fields', '').split():
            if not constants.ID_RX.match(add_field): continue
            if add_field not in views:
                views[add_field] = dict(map=self.MAP_TEMPLATE.format(fieldid=add_field))
        if not views:
            if '_rev' in doc:
                self.db.delete(doc)
        else:
            self.db.save(doc)
        self.see_other('search_fields')