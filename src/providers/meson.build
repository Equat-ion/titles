# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
providersdir = join_paths(pkgdatadir, 'src/providers')

sources = [
  '__init__.py',
  'local_provider.py',
  'stremio_auth.py',
  'stremio_credentials.py',
  'stremio_addon_service.py',
  'stremio_catalog_service.py',
]

install_data(sources, install_dir: providersdir)
