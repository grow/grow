import csv
from . import base
from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient import http
from grow.common import oauth
from grow.common import utils
from grow.preprocessors import google_drive
import datetime
import base64
import httplib2
import json
import logging
import urllib
try:
    import cStringIO as StringIO
except ImportError:
    try:
        import StringIO
    except ImportError:
        from io import StringIO


class AccessLevel(object):
    ADMIN = 'ADMIN'
    READ_AND_COMMENT = 'READ_AND_COMMENT'
    READ_AND_WRITE = 'READ_AND_WRITE'
    READ_ONLY = 'READ_ONLY'


def raise_service_error(http_error, ident=None):
    message = 'HttpError {} for {} returned "{}"'.format(
        http_error.resp.status, http_error.uri,
        http_error._get_reason().strip())
    raise base.TranslatorServiceError(message=message, ident=ident)




class GoogleSheetsTranslator(base.Translator):
    KIND = 'google_sheets'
    has_immutable_translation_resources = False

    def _create_stat_from_response(self, resp, source_lang, lang,
                                   downloaded=False):
        url = resp['alternateLink']
        stat = base.TranslatorStat(
            url=url,
            lang=lang,
#            num_words=resp['numWords'],
#            num_words_translated=resp['numWordsTranslated'],
            source_lang=source_lang,
            ident=resp['id'])
        if downloaded:
            stat.downloaded = datetime.datetime.now()
        else:
            stat.uploaded = datetime.datetime.now()
        return stat

    def _download_content(self, stat):
        sheet_id = stat.ident
        gid = None
        service = google_drive.create_service()
        resp = service.files().get(fileId=sheet_id).execute()
        source_lang = None
        lang = None
        for mimetype, url in resp['exportLinks'].iteritems():
            if not mimetype.endswith('csv'):
                continue
            url += '&gid={}'.format(gid) if gid else ''
            resp, content = service._http.request(url)
            if resp.status != 200:
                raise_service_error(http_error=resp)
            fp = StringIO.StringIO()
            fp.write(content)
            fp.seek(0)
            reader = csv.DictReader(fp)
            # TODO(jeremydw): Implement me.
#            for row in reader:
#                row[0]
        stat = self._create_stat_from_response(
            resp, source_lang, lang, downloaded=True)
        return stat, content

    def _upload_catalog(self, catalog, source_lang):
        project_title = self.project_title
        service = google_drive.create_service()
        lang = str(catalog.locale)
        source_lang = str(source_lang)
        body = {
            'title': project_title,
            'mimeType': 'text/csv',
        }
        fp = StringIO.StringIO()
        writer = csv.writer(fp)
        writer.writerow([source_lang, lang])
        for message in catalog:
            if not message.id:  # Skip header message.
                continue
            source = (message.id.encode('utf-8')
                      if isinstance(message.id, unicode) else message.id)
            translation = (message.string.encode('utf-8')
                           if isinstance(message.string, unicode)
                           else message.string)
            writer.writerow([source, translation])
        fp.seek(0)
        media_body = http.MediaIoBaseUpload(fp, mimetype='text/csv')
        request = service.files().insert(body=body, media_body=media_body)
        request.uri += '&convert=true'
        resp = request.execute()
        return self._create_stat_from_response(resp, source_lang, lang)
