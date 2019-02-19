import sublime
import sublime_plugin
import os
import uuid
import string
import random
import base64
import requests
from subprocess import *
from requests.auth import HTTPBasicAuth

class NpasteUploadCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    settings = sublime.load_settings('npaste.sublime-settings')
    selection = self.view.sel()
    selections = "\n".join(list(map(lambda s: self.view.substr(s), selection)))

    if selections == "":
      npaste_data = self.view.substr(sublime.Region(0, self.view.size()))
    else:
      npaste_data = selections

    data = ""
    passphrase = None
    payload = {'age': settings.get('age') }

    # Encrypt paste using GPG
    if (settings.get('encrypt') == True):
      passphrase = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(settings.get('encryption_key_length')))

      process = Popen(['gpg', '--armor', '--batch', '--passphrase', passphrase, '--symmetric'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
      d = bytes(npaste_data, 'utf-8')
      process.stdin.write(base64.b64encode(bytes(npaste_data, 'utf-8')))
      paste, errs = process.communicate()

      if (not errs):
        data = paste.decode("utf-8")
        payload["encrypted"] = 1
      else:
        sublime.message_dialog(errs.decode("utf-8"))
    else:
      data = npaste_data

    if settings.get('archive') == True:
      payload["archive"] = 1

    # Upload paste to npaste
    files = {'paste': ('paste.txt', data, 'text/plain')}
    r = requests.post(settings.get('url'), files=files, data=payload, auth=HTTPBasicAuth(settings.get('username'), settings.get('password')))

    url = r.text

    if (passphrase is not None):
      url = url + "#" + passphrase

    sublime.set_clipboard(url)
    sublime.message_dialog('Copied to clipboard!')
