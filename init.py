# coding: utf-8
#1. 创建默认角色

import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import re
import time
import getpass
import readline
import django
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.core.management import execute_from_command_line
from django.contrib.auth.models import User
from django.conf import settings

#创建管理员
User.objects.create_superuser('admin', 'admin@example.com', 'password', last_name='admin')
