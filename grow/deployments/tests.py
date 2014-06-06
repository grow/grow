from .destinations import messages
import logging
import os
import texttable


def print_results(results):
  rows, cols = os.popen('stty size', 'r').read().split()
  cols = int(cols)
  table = texttable.Texttable(max_width=0)
  table.set_deco(texttable.Texttable.HEADER)
  table.set_cols_align(['l', 'l', 'l'])
  table.set_cols_width([6, cols * .3, cols * .4])
  rows = []
  rows.append(['', 'Title', 'Message'])
  for message in results.test_results:
    if message.result == messages.Result.PASS:
      color = texttable.bcolors.GREEN
    elif message.result == messages.Result.FAIL:
      color = texttable.bcolors.GREEN
    else:
      color = texttable.bcolors.YELLOW
    label = texttable.get_color_string(color, message.result)
    rows.append([label, message.title, message.text or ''])
  table.add_rows(rows)
  logging.info('\n' + table.draw() + '\n')
