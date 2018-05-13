# -*- coding: utf-8 -*-
"""
/***************************************************************************
 smmt_plugin
                                 A QGIS plugin
 This plugin allows the user to collect features in the photos and store then in file or database
                             -------------------
        begin                : 2018-05-12
        copyright            : (C) 2018 by Lucas Bíscaro
        email                : lucashebiscaro@hotmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load smmt_plugin class from file smmt_plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .smmt_plugin import smmt_plugin
    return smmt_plugin(iface)
