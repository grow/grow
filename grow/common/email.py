from google.appengine.api import mail

SENDER = 'noreply@grow.io'


def send(sender, to, subject, body, html=None):
  if html:
    return mail.send_mail(sender=sender, to=to, subject=subject, body=body, html=html)
  else:
    return mail.send_mail(sender=sender, to=to, subject=subject, body=body)
