# -*- coding: utf-8 -*-
"""
/***************************************************************************
 smmt_plugin
                                 A QGIS plugin
 This plugin allows the user to collect features in the photos and store then in file or database
                              -------------------
        begin                : 2018-05-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Lucas Bíscaro
        email                : lucashebiscaro@hotmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *#QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import * #QAction, QIcon, QFileDialog, QDialog
# Initialize Qt resources from file resources.py
import resources
import glob
# Import the code for the dialog
from smmt_plugin_dialog import smmt_pluginDialog
import os.path


class smmt_plugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'smmt_plugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
#==========================================================================
        # Create the dialog (after translation) and keep reference
        self.dlg = smmt_pluginDialog()
#=======================================================================
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SMMT Features Collector')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'smmt_plugin')
        self.toolbar.setObjectName(u'smmt_plugin')
#===============================================================
        self.dlg.lineEdit_e.clear()
        self.dlg.lineEdit_d.clear()
        self.dlg.pushButton_d.clicked.connect(self.selecionar_fotos_direita)
        self.dlg.pushButton_e.clicked.connect(self.selecionar_fotos_esquerda)
        btn = QPushButton("Quit", self.dlg)
        #btn.clicked.connect(QCoreApplication.instance().quit)
        self.dlg.resize(2000,1000)
        btn2 = QPushButton("Next", self.dlg)
        btn2.resize(btn2.sizeHint())
        btn2.move(100,500)
        btn2.clicked.connect(self.passar_foto)
        self.dlg.cena = QGraphicsScene(self.dlg)
        self.dlg._photo = QGraphicsPixmapItem()
        self.dlg.cena.addItem(self.dlg._photo)
        self.dlg.visu = QGraphicsView(self.dlg)
        self.dlg.visu.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.dlg.visu.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.dlg.visu.setFrameShape(QFrame.NoFrame)
        self.dlg.visu.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dlg.visu.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dlg.visu.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        #self.dlg.visu.setGeometry(300,300,400,400)
        self.dlg.visu.setDragMode(QGraphicsView.ScrollHandDrag)
        self.dlg.visu._zoom = 0
        self.dlg.visu._empty = False
        self.dlg.visu.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)




        #layout = QVBoxLayout()
        #layout.addWidget(self.dlg.visu)
        #self.dlg.label_im_e.setLayout(layout)






#================================================================
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('smmt_plugin', message)
#===============================================================
    #def set_geometry(self,setGeometry):
    #    self.dlg.label_im_d.setGeometry(50,50,500,500)


#==============================================================
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.
        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str
        :param text: Text that should be shown in menu items for this action.
        :type text: str
        :param callback: Function to be called when the action is triggered.
        :type callback: function
        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool
        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool
        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool
        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str
        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget
        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/smmt_plugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'SMMT Feature Colletctor'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SMMT Features Collector'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
#====================================================================

    def selecionar_fotos_esquerda(self):
        #filename_left = QFileDialog.getOpenFileNames(self.dlg, "Selecionar imagens câmera esquerda","/", '*.jpg, *.png')
        filename_left_dir= QFileDialog.getExistingDirectory(self.dlg,"Selecionar Pasta com imagens camera da esquerda","/")
        self.dlg.lineEdit_e.setText(filename_left_dir)

    def hasPhoto(self):
        return not self.dlg.visu._empty

    def fitInView(self,scale=True):
        rect = QRectF(self.dlg._photo.pixmap().rect())
        if not rect.isNull():
            self.dlg.visu.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.dlg.visu.transform().mapRect(QRectF(0,0,1,1))
                self.dlg.visu.scale(1/unity.width(),1/unity.height())
                viewrect = self.dlg.visu.viewport().rect()
                scenerect = self.dlg.visu.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(), viewrect.height() / scenerect.height())
                self.dlg.visu.scale(factor,factor)
            self.dlg.visu._zoom = 0


    def wheelEvent(self,ev):
        if self.hasPhoto():
            if event.delta() > 0:
                factor = 1.25
                self.dlg.visu._zoom += 1
            else:
                factor = 0.8
                self.dlg.visu._zoom -= 1

            if self.dlg.visu._zoom > 0:
                self.dlg.visu.scale(factor, factor)
            elif self.dlg.visu._zoom == 0:
                self.fitInView()
            else:
                self.dlg.visu._zoom = 0

    def selecionar_fotos_direita(self):

        #filename_right = QFileDialog.getOpenFileNames(self.dlg, "Selecionar imagens câmera direita","/", '*.jpg, *.png')
        self.filename_right_dir= QFileDialog.getExistingDirectory(self.dlg,"Selecionar Pasta com imagens camera da direita","/")
        #list of jpeg files inside the folder
        #files = [name for name in os.listdir(str(filename_right_dir)) if name.endswith('.png')]
        self.files = os.listdir(self.filename_right_dir)
        #filename_right = QFileDialog.getOpenFileName(self.dlg,"cuzao","/home/lucas/Imagens")
        #self.dlg.lineEdit_d.setText(filename_right_dir)
        #img = QImage(filename_right)
        #self.dlg.label_im_d.resize(600,600)

        self.index=0
        pixmap = QPixmap(os.path.join(self.filename_right_dir,self.files[self.index])) #.scaled(self.dlg.label_im_d.width(),self.dlg.label_im_d.height(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
        #self.dlg.cena.addPixmap(pixmap)
        self.dlg._photo.setPixmap(pixmap)
        self.dlg.visu.setScene(self.dlg.cena)
        self.fitInView(self)

    def passar_foto(self):
        self.index +=1
        pixmap = QPixmap(os.path.join(self.filename_right_dir,self.files[self.index])) .scaled(self.dlg.label_im_d.width(),self.dlg.label_im_d.height(),Qt.KeepAspectRatio,Qt.SmoothTransformation)




#====================================================================================

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            filename_left = self.dlg.lineEdit_e.text()
            filename_right = self.dlg.lineEdit_d.text()
