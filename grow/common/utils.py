import re
import yaml


def memoize(f):
  class memodict(dict):
    def __init__(self, f):
      self.f = f
    def __call__(self, *args):
      return self[args]
    def __missing__(self, key):
      ret = self[key] = self.f(*key)
      return ret
  return memodict(f)


def parse_yaml(content):
  content = content.strip()
  parts = re.split('---\n', content)
  if len(parts) == 1:
    return yaml.load(content), None
  parts.pop(0)
  front_matter, body = parts
  parsed_yaml = yaml.load(front_matter)
  body = str(body)
  return parsed_yaml, body
