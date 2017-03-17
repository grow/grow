from . import build
from . import convert
from . import deploy
from . import download_translations
from . import extract
from . import filter
from . import import_translations
from . import init
from . import install
from . import machine_translate
from . import preprocess
from . import routes
from . import run
from . import stage
from . import stats
from . import upload_translations


def add(group):
    group.add_command(build.build)
    group.add_command(convert.convert)
    group.add_command(deploy.deploy)
    group.add_command(download_translations.download_translations)
    group.add_command(extract.extract)
    group.add_command(filter.filter)
    group.add_command(import_translations.import_translations)
    group.add_command(init.init)
    group.add_command(machine_translate.machine_translate)
    group.add_command(preprocess.preprocess)
    group.add_command(routes.routes)
    group.add_command(run.run)
    group.add_command(install.install)
    group.add_command(stats.stats)
    group.add_command(stage.stage)
    group.add_command(upload_translations.upload_translations)
