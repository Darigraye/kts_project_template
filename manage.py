import sys

from main import main as run_app
from kts_backend.store.vk_api.poller import run_poller
from kts_backend.store.bot.manager import run_manager
from kts_backend.store.vk_api.sender import run_sender


FUNCTIONS_FOR_RUNNING = {
    'run_app': run_app,
    'run_poller': run_poller,
    'run_manager': run_manager,
    'run_sender': run_sender
                         }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Number arguments of the script must be equally 2')

    if sys.argv[1] in FUNCTIONS_FOR_RUNNING:
        func = FUNCTIONS_FOR_RUNNING[sys.argv[1]]
        func()
    else:
        raise Exception(f'function with name {sys.argv[1]} doesnt exists')
