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
import csv


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

        #self.dlg.tableWidget.horizontalHeaderItem().setTextAlignment(Qt.AlignHCenter)
        #self.dlg.tableWidget.setReadOnly(True)

        self.dlg.pushButton_d.clicked.connect(self.selecionar_fotos_direita)
        self.dlg.pushButton_e.clicked.connect(self.selecionar_fotos_esquerda)

        self.dlg.resize(1000,650)

        #BOTÕES
        self.dlg.bproxima = QPushButton("PROXIMA", self.dlg)
        self.dlg.banterior = QPushButton("ANTERIOR", self.dlg)
        self.dlg.bpoe = QPushButton("POE", self.dlg)

        self.dlg.bproxima.clicked.connect(self.passar_foto)
        self.dlg.banterior.clicked.connect(self.voltar_foto)
        self.dlg.bpoe.clicked.connect(self.ler_arquivo_texto)


        self.dlg.bproxima.setEnabled(False)
        self.dlg.banterior.setEnabled(False)

        #Botões Direita
        bzoomin_d = QPushButton("+", self.dlg)
        bzoomout_d = QPushButton("-", self.dlg)
        bfitinview_d = QPushButton("o", self.dlg)

        bzoomin_d.clicked.connect(self.zoomin_d)
        bzoomout_d.clicked.connect(self.zoomout_d)
        bfitinview_d.clicked.connect(self.fitInView_d)

        #Botões Esquerda
        bzoomin_e = QPushButton("+", self.dlg)
        bzoomout_e = QPushButton("-", self.dlg)
        bfitinview_e = QPushButton("o", self.dlg)

        bzoomin_e.clicked.connect(self.zoomin_e)
        bzoomout_e.clicked.connect(self.zoomout_e)
        bfitinview_e.clicked.connect(self.fitInView_e)


        #Janelas Direta(r) e esquerda(l)
        self.dlg.cena_d = QGraphicsScene(self.dlg)
        self.dlg.cena_e = QGraphicsScene(self.dlg)

        self.dlg._photo_d = QGraphicsPixmapItem()
        self.dlg._photo_e = QGraphicsPixmapItem()

        self.dlg.cena_d.addItem(self.dlg._photo_d)
        self.dlg.cena_e.addItem(self.dlg._photo_e)

        self.dlg.visu_d = QGraphicsView(self.dlg)
        self.dlg.visu_e = QGraphicsView(self.dlg)

        self.dlg.visu_d.setScene(self.dlg.cena_d)
        self.dlg.visu_e.setScene(self.dlg.cena_e)

        self.dlg.visu_d.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.dlg.visu_e.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.dlg.visu_d.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.dlg.visu_e.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.dlg.visu_d.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dlg.visu_e.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.dlg.visu_d.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dlg.visu_e.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.dlg.visu_d.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.dlg.visu_e.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.dlg._zoom_d = 0
        self.dlg._zoom_e = 0

        self.dlg._empty_d = True
        self.dlg._empty_e = True

        self.dlg.visu_d.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)
        self.dlg.visu_e.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)

        self.dlg.editPixInfo_d = QLineEdit(self.dlg)
        self.dlg.editPixInfo_e = QLineEdit(self.dlg)

        self.dlg.editPixInfo_d.setReadOnly(True)
        self.dlg.editPixInfo_e.setReadOnly(True)

        #Agrupando objetos em um mesmo layout (direita e esqueda)
        vertical_e = QWidget(self.dlg)
        vertical_e.setGeometry(QRect(30,150,900,450))
        vertical_e.setObjectName("Camera esquerda")
        HBlayout_e = QHBoxLayout(vertical_e)
        VBlayout_e1 = QVBoxLayout()
        VBlayout_e1.addWidget(self.dlg.visu_e)
        VBlayout_e2 = QVBoxLayout()
        VBlayout_e2.addWidget(self.dlg.bproxima)
        VBlayout_e2.addWidget(self.dlg.banterior)
        HBlayout_e3 = QHBoxLayout()
        HBlayout_e3.setAlignment(Qt.AlignLeft)
        HBlayout_e3.addWidget(bzoomin_e)
        HBlayout_e3.addWidget(bzoomout_e)
        HBlayout_e3.addWidget(bfitinview_e)
        HBlayout_e3.addWidget(self.dlg.editPixInfo_e)
        VBlayout_e1.addLayout(HBlayout_e3)
        HBlayout_e.addLayout(VBlayout_e1)
        HBlayout_e.addLayout(VBlayout_e2)

        VBlayout_d1 = QVBoxLayout()
        VBlayout_d1.addWidget(self.dlg.visu_d)
        HBlayout_d3 = QHBoxLayout()
        HBlayout_d3.setAlignment(Qt.AlignLeft)
        HBlayout_d3.addWidget(bzoomin_d)
        HBlayout_d3.addWidget(bzoomout_d)
        HBlayout_d3.addWidget(bfitinview_d)
        HBlayout_d3.addWidget(self.dlg.editPixInfo_d)
        VBlayout_d1.addLayout(HBlayout_d3)
        HBlayout_e.addLayout(VBlayout_d1)




        #Algumas consideraçãoes iniciais
        self.dlg.pixmap_left = 0
        self.dlg.pixmap_eight = 0

        self.filename_right_dir = 0
        self.filename_left_dir = 0

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
    def hasPhoto_d(self):
        return not self.dlg._empty_d

    def hasPhoto_e(self):
        return not self.dlg._empty_e

    def fitInView_d(self, scale=True):
        rect_d = QRectF(self.dlg._photo_d.pixmap().rect())
        if not rect_d.isNull():
            self.dlg.visu_d.setSceneRect(rect_d)
            if self.hasPhoto_d():
                unity_d = self.dlg.visu_d.transform().mapRect(QRectF(0,0,1,1))
                self.dlg.visu_d.scale(1/unity_d.width(),1/unity_d.height())
                viewrect_d = self.dlg.visu_d.viewport().rect()
                scenerect_d = self.dlg.visu_d.transform().mapRect(rect_d)
                self.dlg.factor_d = min(viewrect_d.width() / scenerect_d.width(), viewrect_d.height() / scenerect_d.height())
                self.dlg.visu_d.scale(self.dlg.factor_d,self.dlg.factor_d)
            self.dlg._zoom_d = 0

    def fitInView_e(self, scale=True):
        rect_e = QRectF(self.dlg._photo_e.pixmap().rect())
        if not rect_e.isNull():
            self.dlg.visu_e.setSceneRect(rect_e)
            if self.hasPhoto_e():
                unity_e = self.dlg.visu_e.transform().mapRect(QRectF(0,0,1,1))
                self.dlg.visu_e.scale(1/unity_e.width(),1/unity_e.height())
                viewrect_e = self.dlg.visu_e.viewport().rect()
                scenerect_e = self.dlg.visu_e.transform().mapRect(rect_e)
                self.dlg.factor_e = min(viewrect_e.width() / scenerect_e.width(), viewrect_e.height() / scenerect_e.height())
                self.dlg.visu_e.scale(self.dlg.factor_e,self.dlg.factor_e)
            self.dlg._zoom_e = 0

    def zoomin_d(self):
        self.dlg.visu_d.scale(1.2,1.2)

    def zoomin_e(self):
        self.dlg.visu_e.scale(1.2,1.2)

    def zoomout_d(self):
        self.dlg.visu_d.scale(0.8,0.8)

    def zoomout_e(self):
        self.dlg.visu_e.scale(0.8,0.8)

    def setPhoto_left(self, pixmap=None):
        self.dlg._zoom_e = 0
        if self.dlg.pixmap_left and not self.dlg.pixmap_left.isNull():
            self.dlg._empty_e = False
            self.dlg._photo_e.setPixmap(self.dlg.pixmap_left)
            self.dlg.visu_e.setDragMode(QGraphicsView.ScrollHandDrag)
            self.dlg._photo_e.mouseDoubleClickEvent = self.pixelSelect_e
            self.dlg.editPixInfo_e.clear()

        else:
            self.dlg._empty_e = True
            self.dlg.visu_e.setDragMode(QGraphicsView.NoDrag)
            self.dlg._photo_e.setPixmap(QPixmap())
        self.fitInView_e()

    def setPhoto_right(self, pixmap=None):
        self.dlg._zoom_d = 0
        if self.dlg.pixmap_right and not self.dlg.pixmap_right.isNull():
            self.dlg._empty_d = False
            self.dlg._photo_d.setPixmap(self.dlg.pixmap_right)
            self.dlg.visu_d.setDragMode(QGraphicsView.ScrollHandDrag)
            self.dlg._photo_d.mouseDoubleClickEvent = self.pixelSelect_d
            self.dlg.editPixInfo_d.clear()

        else:
            self.dlg._empty_d = True
            self.dlg.visu_d.setDragMode(QGraphicsView.NoDrag)
            self.dlg._photo_d.setPixmap(QPixmap())
        self.fitInView_d()

    def selecionar_fotos_direita(self):
        self.index=0
        self.dlg.lineEdit_d.clear()
        #filename_right = QFileDialog.getOpenFileNames(self.dlg, "Selecionar imagens câmera direita","/", '*.jpg, *.png')
        self.filename_right_dir =  QFileDialog.getExistingDirectory(self.dlg,"Selecionar pasta com imagens camera da direita","/")


        #filename_right = QFileDialog.getOpenFileName(self.dlg,"cuzao","/home/lucas/Imagens")
        #self.dlg.lineEdit_d.setText(filename_right_dir)
        #img = QImage(filename_right)
        #self.dlg.label_im_d.resize(600,600)

        if self.filename_right_dir != '':
            self.files_right = sorted(os.listdir(self.filename_right_dir))
            self.dlg.pixmap_right = QPixmap(os.path.join(self.filename_right_dir,self.files_right[self.index]))
            self.setPhoto_right(self.dlg.pixmap_right)
            self.dlg.lineEdit_d.setText(self.filename_right_dir)
            self.habilitarbotao()

    def selecionar_fotos_esquerda(self):
        self.index=0
        self.dlg.lineEdit_e.clear()
        self.filename_left_dir = QFileDialog.getExistingDirectory(self.dlg,"Selecionar Pasta com imagens camera da esquerda","/")

        if self.filename_right_dir != '':
            self.files_left = sorted(os.listdir(self.filename_left_dir))
            self.dlg.pixmap_left = QPixmap(os.path.join(self.filename_left_dir,self.files_left[self.index]))
            self.setPhoto_left(self.dlg.pixmap_left)
            self.dlg.lineEdit_e.setText(self.filename_left_dir)
            self.habilitarbotao()

    def passar_foto(self):
        self.index += 1

        if self.index >= len(self.files_left) and self.index >= len(self.files_right):
            self.index = len(self.files_left)
            self.index = len(self.files_right)

        else:
            self.dlg.pixmap_left = QPixmap(os.path.join(self.filename_left_dir,self.files_left[self.index]))
            self.dlg.visu_e.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setPhoto_left(self.dlg.pixmap_left)
            self.fitInView_e(self)
            self.dlg.editPixInfo_e.clear()

            self.dlg.pixmap_right = QPixmap(os.path.join(self.filename_right_dir,self.files_right[self.index]))
            self.dlg.visu_d.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setPhoto_right(self.dlg.pixmap_right)
            self.fitInView_d(self)
            self.dlg.editPixInfo_d.clear()

    def voltar_foto(self):
        self.index -=1

        if self.index <= 0:
            self.index = 0
            self.dlg.pixmap_left = QPixmap(os.path.join(self.filename_left_dir,self.files_left[self.index]))
            self.dlg.visu_e.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setPhoto_left(self.dlg.pixmap_left)
            self.fitInView_e(self)
            self.dlg.editPixInfo_e.clear()

            self.dlg.pixmap_right = QPixmap(os.path.join(self.filename_right_dir,self.files_right[self.index]))
            self.dlg.visu_d.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setPhoto_right(self.dlg.pixmap_right)
            self.fitInView_d(self)
            self.dlg.editPixInfo_d.clear()

        else:
            self.dlg.pixmap_left = QPixmap(os.path.join(self.filename_left_dir,self.files_left[self.index]))
            self.dlg.visu_e.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setPhoto_left(self.dlg.pixmap_left)
            self.fitInView_e(self)
            self.dlg.editPixInfo_e.clear()

            self.dlg.pixmap_right = QPixmap(os.path.join(self.filename_right_dir,self.files_right[self.index]))
            self.dlg.visu_d.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setPhoto_right(self.dlg.pixmap_right)
            self.fitInView_d(self)
            self.dlg.editPixInfo_d.clear()

    def pixelSelect_d(self,event):
        position_d = QPoint( event.pos().x(),  event.pos().y())
        self.dlg.editPixInfo_d.setText('%d, %d' % (event.pos().x(), event.pos().y()))

    def pixelSelect_e(self,event):
        position_e = QPoint( event.pos().x(),  event.pos().y())
        self.dlg.editPixInfo_e.setText('%d, %d' % (event.pos().x(), event.pos().y()))

    def habilitarbotao(self):
        if self.dlg.pixmap_left == 0 or self.dlg.pixmap_right == 0:
            self.dlg.bproxima.setEnabled(False)
            self.dlg.banterior.setEnabled(False)

        else:
            self.dlg.bproxima.setEnabled(True)
            self.dlg.banterior.setEnabled(True)

    def ler_arquivo_texto(self):
        name = QFileDialog.getOpenFileName(self.dlg,"Selecionar os parametros de orietacao exterior","/")

        texto = []
        reader = csv.reader(open(name), delimiter = ',')
        for row in reader:
            texto.append(row)

        rowCount = len(texto)
        colCount = max([len(p) for p in texto])

        self.dlg.tableWidget.setRowCount(rowCount)
        self.dlg.tableWidget.setColumnCount(colCount)

        self.dlg.tableWidget.setHorizontalHeaderLabels(('ID_Foto','Longitude','Latitude','Altitude','X0','Y0','Z0','omega','phy','kappa','bla1','bla2','bla3'))

        for row, foto in enumerate(texto):
            for column, value in enumerate(foto):
                newItem = QTableWidgetItem(value)
                newItem.setFlags(Qt.ItemIsEnabled)
                self.dlg.tableWidget.setItem(row, column, newItem)

    #descobrir uma maneira de resetar tudo quando fechado
    def reset(self):
        self.dlg.cena_d = QGraphicsScene(self.dlg)
        self.dlg.cena_e = QGraphicsScene(self.dlg)

        self.dlg._photo_d = QGraphicsPixmapItem()
        self.dlg._photo_e = QGraphicsPixmapItem()

        self.dlg.cena_d.addItem(self.dlg._photo_d)
        self.dlg.cena_e.addItem(self.dlg._photo_e)

        self.dlg.visu_d = QGraphicsView(self.dlg)
        self.dlg.visu_e = QGraphicsView(self.dlg)

        self.dlg.visu_d.setScene(self.dlg.cena_d)
        self.dlg.visu_e.setScene(self.dlg.cena_e)

        self.dlg.visu_d.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.dlg.visu_e.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.dlg.visu_d.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.dlg.visu_e.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.dlg.visu_d.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dlg.visu_e.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.dlg.visu_d.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dlg.visu_e.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.dlg.visu_d.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.dlg.visu_e.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.dlg._zoom_d = 0
        self.dlg._zoom_e = 0

        self.dlg._empty_d = True
        self.dlg._empty_e = True



#====================================================================================

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        #if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            #filename_left = self.dlg.lineEdit_e.text()
            #filename_right = self.dlg.lineEdit_d.text()
