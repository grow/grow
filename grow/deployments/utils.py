import os
from git import config


def get_git_username():
  config_path = '/Users/jeremydw/.gitconfig'
  return config.GitConfigParser(config_path).get('user', 'email')


def get_git_email():
  config_path = '/Users/jeremydw/.gitconfig'
  return config.GitConfigParser(config_path).get('user', 'email')
