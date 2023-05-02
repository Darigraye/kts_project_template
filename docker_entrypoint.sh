#!/bin/bash

python manage.py run_app &
python manage.py run_vk_api &
python manage.py run_poller &
python manage.py run_sender &