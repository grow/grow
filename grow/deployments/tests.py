from .destinations import messages
import logging
import texttable


def print_results(results):
    for message in results.test_results:
        if message.result == messages.Result.PASS:
            color = texttable.bcolors.GREEN
        elif message.result == messages.Result.FAIL:
            color = texttable.bcolors.GREEN
        else:
            color = texttable.bcolors.YELLOW
        label = texttable.get_color_string(color, message.result)
        logging.info('{} {}'.format(label, message.title))
