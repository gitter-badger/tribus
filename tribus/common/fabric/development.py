#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Desarrolladores de Tribus
#
# This file is part of Tribus.
#
# Tribus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tribus is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import pwd
import sys
import site
import urllib
# import lsb_release
from fabric.api import local, env, settings, cd
from tribus import BASEDIR
from tribus.config.base import PACKAGECACHE
from tribus.config.ldap import (AUTH_LDAP_SERVER_URI, AUTH_LDAP_BASE,
                                AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD)
from tribus.config.pkg import (debian_system_dependencies,
                               debian_docker_dependencies)
from tribus.common.logger import get_logger
from tribus.config.waffle_cfg import SWITCHES_CONFIGURATION

logger = get_logger()


def development():
    # env.user = pwd.getpwuid(os.getuid()).pw_name
    # env.root = 'root'
    # env.environment = 'development'
    # env.hosts = ['localhost']
    # env.virtualenv_dir = os.path.join(env.basedir, 'virtualenv')
    # env.virtualenv_cache = os.path.join(BASEDIR, 'virtualenv_cache')
    # env.virtualenv_site_dir = os.path.join(
    #     env.virtualenv_dir, 'lib', 'python%s' %
    #     sys.version[:3], 'site-packages')
    # env.virtualenv_args = ' '.join(['--clear', '--no-site-packages',
    #                                 '--setuptools', '--unzip-setuptools'])
    # env.virtualenv_activate = os.path.join(
    #     env.virtualenv_dir, 'bin', 'activate')
    # env.settings = 'tribus.config.web'
    # env.sudo_prompt = 'Executed'
    # env.f_python_dependencies = f_python_dependencies
    # env.xapian_destdir = os.path.join(
    #     env.virtualenv_dir, 'lib', 'python%s' %
    #     sys.version[:3], 'site-packages', 'xapian')
    # env.xapian_init = os.path.join(
    #     os.path.sep,
    #     'usr',
    #     'share',
    #     'pyshared',
    #     'xapian',
    #     '__init__.py')
    # env.xapian_so = os.path.join(
    #     os.path.sep,
    #     'usr',
    #     'lib',
    #     'python%s' % sys.version[:3],
    #     'dist-packages',
    #     'xapian',
    #     '_xapian.so')
    # env.reprepro_dir = os.path.join(BASEDIR, 'test_repo')
    # env.sample_packages_dir = os.path.join(BASEDIR, 'package_samples')
    # env.distributions_path = os.path.join(BASEDIR, 'tribus', 'config',
    #                                       'data', 'dists-template')
    # env.selected_packages = os.path.join(BASEDIR, 'tribus', 'config',
    #                                      'data', 'selected_packages.list')
    # env.f_workenv_preseed = f_workenv_preseed
    env.basedir = BASEDIR

    # System Config
    env.debian_system_dependencies = ' '.join(debian_system_dependencies)
    env.apt_args = ('-o Apt::Install-Recommends=false '
                    '-o Apt::Get::Assume-Yes=true '
                    '-o Apt::Get::AllowUnauthenticated=true '
                    '-o DPkg::Options::=--force-confmiss '
                    '-o DPkg::Options::=--force-confnew '
                    '-o DPkg::Options::=--force-overwrite '
                    '-o DPkg::Options::=--force-unsafe-io')
    env.acquire_proxy = ('-o Acquire::http::proxy=http://localhost:3142 ')

    # Docker config
    env.docker_basedir = '/media/tribus'
    env.docker_debconf_preseed_file = os.path.join(env.docker_basedir, 'tribus', 'config', 'data', 'preseed-debconf.conf')
    env.debian_docker_dependencies = ' '.join(debian_docker_dependencies)
    env.docker_base_image = 'luisalejandro/debian-i386:wheezy'
    env.docker_base_image_id = '5d678e6ce33c'
    env.docker_container = 'container'
    env.docker_env_image = 'environment'
    env.docker_env_vol = ('--volume /var/cache/apt-cacher-ng:/var/cache/apt-cacher-ng:rw '
                          '--volume /var/cache/apt:/var/cache/apt:rw '
                          '--volume %(basedir)s:%(docker_basedir)s:rw') % env
    env.docker_env_args = ('--env DEBIAN_FRONTEND=noninteractive')
    env.docker_env_packages = 'eatmydata apt-cacher-ng'


def environment():
    local_configure_sudo()
    docker_pull_base_image()
    docker_preseed_packages()
    # docker_install_packages(env.docker_env_image,
    #                         env.debian_docker_dependencies)
    # docker_drop_mongo(env.docker_image)
    # docker_configure_postgres(env.docker_image)
    # populate_ldap()
    # create_virtualenv()
    # include_xapian()
    # update_virtualenv()
    # configure_django()
    # deconfigure_sudo()


def local_configure_sudo():
    local(('su root -c '
           '"echo \'%(user)s ALL= NOPASSWD: ALL\' '
           '> /etc/sudoers.d/tribus"') % env, capture=False)


def docker_pull_base_image():

    containers = local(('sudo /bin/bash -c "docker.io ps -aq"'), capture=True)

    if containers:
        local(('sudo /bin/bash -c '
               '"docker.io rm -fv %s"') % containers.replace('\n', ' '),
              capture=False)

    if env.docker_base_image_id not in local(('sudo /bin/bash -c '
                                              '"docker.io images -aq"'),
                                             capture=True):
        local(('sudo /bin/bash -c '
               '"docker.io pull %(docker_base_image)s"') % env, capture=False)

    local(('sudo /bin/bash -c '
           '"docker.io run '
           '--name %(docker_container)s '
           '%(docker_env_args)s '
           '%(docker_env_vol)s '
           '%(docker_base_image)s '
           'apt-get install '
           '%(apt_args)s '
           '%(docker_env_packages)s"') % env, capture=False)

    local(('sudo /bin/bash -c '
           '"docker.io commit '
           '%(docker_container)s %(docker_env_image)s"') % env, capture=False)

    local(('sudo /bin/bash -c '
          '"docker.io rm -fv %(docker_container)s"') % env, capture=False)


def docker_preseed_packages():
    local(('sudo /bin/bash -c '
           '"docker.io run '
           '--name %(docker_container)s '
           '%(docker_env_args)s '
           '%(docker_env_vol)s '
           '%(docker_base_image)s '
           'debconf-set-selections '
           '%(docker_debconf_preseed_file)s"') % env, capture=False)

    local(('sudo /bin/bash -c '
           '"docker.io commit '
           '%(docker_container)s %(docker_env_image)s"') % env, capture=False)

    local(('sudo /bin/bash -c '
          '"docker.io rm -fv %(docker_container)s"') % env, capture=False)

    # local(('sudo /bin/bash -c '
    #       '"docker.io run '
    #       '--env DEBIAN_FRONTEND=noninteractive '
    #       '%s '
    #       'echo \'slapd slapd/purge_database boolean true\' '
    #       '| debconf-set-selections"') % image, capture=False)

    # local(('sudo /bin/bash -c '
    #       '"docker.io run '
    #       '--env DEBIAN_FRONTEND=noninteractive '
    #       '%s '
    #       'echo \'slapd slapd/domain string tribus.org\' '
    #       '| debconf-set-selections"') % image, capture=False)

    # local(('sudo /bin/bash -c '
    #       '"docker.io run '
    #       '--env DEBIAN_FRONTEND=noninteractive '
    #       '%s '
    #       'echo \'slapd shared/organization string tribus\' '
    #       '| debconf-set-selections"') % image, capture=False)

    # local(('sudo /bin/bash -c '
    #       '"docker.io run '
    #       '--env DEBIAN_FRONTEND=noninteractive '
    #       '%s '
    #       'echo \'slapd slapd/password1 password tribus\' '
    #       '| debconf-set-selections"') % image, capture=False)

    # local(('sudo /bin/bash -c '
    #       '"docker.io run '
    #       '--env DEBIAN_FRONTEND=noninteractive '
    #       '%s '
    #       'echo \'slapd slapd/password2 password tribus\' '
    #       '| debconf-set-selections"') % image, capture=False)


def docker_install_packages(image, dependencies):
    local(('sudo /bin/bash -c '
          '"docker.io run '
          '--env DEBIAN_FRONTEND=noninteractive '
          '%s '
          'aptitude install '
          '-o Aptitude::CmdLine::Assume-Yes=true '
          '-o Aptitude::CmdLine::Ignore-Trust-Violations=true '
          '-o DPkg::Options::=--force-confmiss '
          '-o DPkg::Options::=--force-confnew '
          '-o DPkg::Options::=--force-overwrite '
          '-o DPkg::Options::=--force-unsafe-io '
          '%s"') % (image, dependencies), capture=False)


# def docker_drop_mongo(image, db):
#     local(('sudo /bin/bash -c '
#           '"docker.io run '
#           '--env DEBIAN_FRONTEND=noninteractive '
#           '%s '
#           'mongo %s --eval \'db.dropDatabase()\'"') % (image, db), capture=False)


# def docker_configure_postgres(image, pg_user, pg_passwd):
#     local(('sudo /bin/bash -c '
#           '"docker.io run '
#           '--env DEBIAN_FRONTEND=noninteractive '
#           '%s '
#           'echo \'%s:%s\' | chpasswd"') % (image, pg_user, pg_passwd),
#           capture=False)

#     local(('sudo /bin/bash -c '
#           '"docker.io run '
#           '--env DEBIAN_FRONTEND=noninteractive '
#           '%s '
#           'sudo -i -u postgres /bin/sh -c '
#           '\'psql -f /tmp/preseed-db.sql\'"') % (pg_user, pg_passwd), capture=False)


# DROP DATABASE IF EXISTS test_tribus;
# DROP DATABASE IF EXISTS tribus;
# DROP ROLE IF EXISTS tribus;
# CREATE ROLE tribus PASSWORD 'md51a2031d64cd6f9dd4944bac9e73f52dd' NOSUPERUSER CREATEDB CREATEROLE INHERIT LOGIN;
# CREATE DATABASE tribus OWNER tribus;
# GRANT ALL PRIVILEGES ON DATABASE tribus to tribus;
