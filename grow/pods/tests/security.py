from . import base
from . import messages


builtins = {
    'avoid_eval':
        messages.RegExTestMessage(
            text='Avoid `eval` statement.',
            status=messages.Status.WARN,
            regex='eval\(',
        ),
    'avoid_innerhtml':
        messages.RegExTestMessage(
            text='Avoid `innerHTML`. Use `node.textContent` instead.',
            status=messages.Status.WARN,
            regex='\.innerHTML',
        ),
}


class SecurityTestCase(base.RegExTestCase):
  checks = [
      builtins['avoid_eval'],
      builtins['avoid_innerhtml'],
  ]
