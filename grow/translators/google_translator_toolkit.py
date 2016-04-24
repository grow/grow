from . import base
from googleapiclient import discovery
from googleapiclient import errors
from grow.common import oauth
from grow.common import utils
import datetime
import base64
import httplib2
import json
import logging
import urllib

EDIT_URL_FORMAT = 'https://translate.google.com/toolkit/workbench?did={}'
GTT_DOCUMENTS_BASE_URL = 'https://www.googleapis.com/gte/v1/documents'
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gte'
STORAGE_KEY = 'Grow SDK - Google Translator Toolkit'


class AccessLevel(object):
    ADMIN = 'ADMIN'
    READ_AND_COMMENT = 'READ_AND_COMMENT'
    READ_AND_WRITE = 'READ_AND_WRITE'
    READ_ONLY = 'READ_ONLY'


class ChangeType(object):
    MODIFY = 'MODIFY'
    ADD = 'ADD'


def raise_api_error(resp):
    # TODO: Create and use base error class.
    resp = json.loads(resp.content)['error']
    logging.error('GTT Request Error {}: {}'.format(resp['code'], resp['message']))
    for each_error in resp['errors']:
        logging.error('{}: {}'.format(each_error['message'], each_error['reason']))
    raise


class Gtt(object):

    def __init__(self):
        self.service = discovery.build('gte', 'v1', http=self.http)

    @property
    def http(self):
        credentials = oauth.get_credentials(
            scope=OAUTH_SCOPE, storage_key=STORAGE_KEY)
        http = httplib2.Http(ca_certs=utils.get_cacerts_path())
        http = credentials.authorize(http)
        return http

    def get_document(self, document_id):
        return self.service.documents().get(documentId=document_id).execute()

    def get_user_from_acl(self, document_id, email):
        document = self.get_document(document_id)
        for user in document['gttAcl']:
            if user.get('emailId') == email:
                return user

    def update_acl(self, document_id, email, access_level, can_reshare=True,
                   update=False):
        acl_change_type = ChangeType.MODIFY if update else ChangeType.ADD
        body = {
            'gttAclChange': {
                [
                    {
                        'accessLevel': access_level,
                        'canReshare': can_reshare,
                        'emailId': email,
                        'type': acl_change_type,
                    }
                ]
            }
        }
        return self.service.documents().update(
            documentId=document_id, body=body).execute()

    def share_document(self, document_id, email,
                       access_level=AccessLevel.READ_AND_WRITE):
        in_acl = self.get_user_from_acl(document_id, email)
        update = True if in_acl else False
        return self.update_acl(document_id, email,
                               access_level=access_level, update=update)

    def insert_document(self, name, content, source_lang, lang, mimetype,
                        acl=None):
        content = base64.urlsafe_b64encode(content)
        doc = {
            'displayName': name,
            'gttAcl': acl,
            'language': lang,
            'mimetype': mimetype,
            'sourceDocBytes': content,
            'sourceLang': source_lang,
        }
        if acl:
            doc['gttAcl'] = acl
        try:
            return self.service.documents().insert(body=doc).execute()
        except errors.HttpError as resp:
            raise_api_error(resp)

    def download_document(self, document_id):
        params = {
            'alt': 'media',
            'downloadContent': True,
        }
        url = '{}/{}?{}'.format(
            GTT_DOCUMENTS_BASE_URL,
            urllib.quote(document_id), urllib.urlencode(params))
        response, content = self.http.request(url)
        # TODO: Create and use base error class.
        try:
            if response.status >= 400:
                raise errors.HttpError(response, content, uri=url)
        except errors.HttpError as resp:
            raise_api_error(resp)
        return content


class GoogleTranslatorToolkitTranslator(base.Translator):
    KIND = 'google_translator_toolkit'

    def _normalize_source_lang(self, source_lang):
        if source_lang is None:
            return 'en'
        source_lang = str(source_lang)
        source_lang = source_lang.lower()
        if source_lang == 'en_us':
            return 'en'
        return source_lang

    def _download_content(self, stat):
        gtt = Gtt()
        content = gtt.download_document(stat.ident)
        return content

    def _upload_catalog(self, catalog, source_lang):
        gtt = Gtt()
        project_title = self.project_title
        name = '{} ({})'.format(project_title, str(catalog.locale))
        source_lang = self._normalize_source_lang(source_lang)
        acl = None
        if 'acl' in self.config:
            acl = []
            for item in self.config['acl']:
                access_level = item.get('access_level',
                                        AccessLevel.READ_AND_WRITE)
                acl.append({
                    'emailId': item['email'],
                    'accessLevel': access_level
                })
        lang = str(catalog.locale)
        resp = gtt.insert_document(
            name=name,
            content=catalog.content,
            source_lang=str(source_lang),
            lang=lang,
            mimetype='text/x-gettext-translation',
            acl=acl)
        edit_url = EDIT_URL_FORMAT.format(resp['id'])
        stat = base.TranslatorStat(
            edit_url=edit_url,
            lang=lang,
            num_words=resp['numWords'],
            num_words_translated=resp['numWordsTranslated'],
            source_lang=source_lang,
            created=datetime.datetime.now(),
            ident=resp['id'])
        return stat
