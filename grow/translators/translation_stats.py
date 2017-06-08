import gettext


class TranslationStats(object):

    def __init__(self):
        self._locale_to_message = {}
        self._untranslated = {}

    @property
    def messages(self):
        return self._locale_to_message

    @property
    def untranslated(self):
        tracking = {}
        for locale, messages in self._untranslated.iteritems():
            if locale not in tracking:
                tracking[locale] = {}
            for message in messages:
                tracking[locale][message] = self._locale_to_message[locale][message]
        return tracking

    def export(self):
        return {
            'messages': self.messages,
            'untranslated': self.untranslated,
        }

    def tick(self, message, locale):
        if locale not in self._locale_to_message:
            self._locale_to_message[locale] = {}

        messages = self._locale_to_message[locale]
        if message.id not in messages:
            messages[message.id] = 0
        messages[message.id] += 1

        if not message.string:
            if locale not in self._untranslated:
                self._untranslated[locale] = set()
            self._untranslated[locale].add(message.id)
