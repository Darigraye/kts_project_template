import sys

from main import main as run_app
from adminapi_run import run_admin_api
from kts_backend.store.vk_api.poller import run_poller
from kts_backend.store.vk_api.sender import run_sender
from kts_backend.store.vk_api.accessor import run_vk_api


FUNCTIONS_FOR_RUNNING = {
    'run_app': run_app,
    'run_poller': run_poller,
    'run_vk_api': run_vk_api,
    'run_sender': run_sender,
    'run_admin': run_admin_api
                         }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Number arguments of the script must be equally 2')

    if sys.argv[1] in FUNCTIONS_FOR_RUNNING:
        func = FUNCTIONS_FOR_RUNNING[sys.argv[1]]
        func()
    else:
        raise Exception(f'function with name {sys.argv[1]} doesnt exists')
