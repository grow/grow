import logging

from grow.common import tables as texttable

from .destinations import messages


def print_results(results):
    for message in results.test_results:
        if message.result == messages.Result.PASS or message.result == messages.Result.FAIL:
            color = texttable.bcolors.GREEN
        else:
            color = texttable.bcolors.YELLOW
        label = texttable.get_color_string(color, message.result)
        logging.info(f'{label} {message.title}')
