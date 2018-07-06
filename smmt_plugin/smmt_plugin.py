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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import resources
import glob
from smmt_plugin_dialog import smmt_pluginDialog
import os.path
import csv
import numpy as np
import math
import pyproj
import processing
import qgis.utils

class smmt_plugin:

    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: Qgisinterface
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

        # Create the dialog (after translation) and keep reference
        self.dlg = smmt_pluginDialog()


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SMMT Features Collector')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'smmt_plugin')
        self.toolbar.setObjectName(u'smmt_plugin')


        #Limpar os campos
        self.dlg.lineEdit_e.clear()
        self.dlg.lineEdit_d.clear()
        self.dlg.lineEdit.clear()


        #Conecta com as funções
        self.dlg.pushButton_d.clicked.connect(self.selecionar_fotos_direita)
        self.dlg.pushButton_e.clicked.connect(self.selecionar_fotos_esquerda)


        #Tamanho da tela do plugin
        self.dlg.resize(960,760)


        #BOTÕES
        self.dlg.bproxima = QPushButton("PROXIMA", self.dlg)
        self.dlg.banterior = QPushButton("ANTERIOR", self.dlg)
        self.dlg.bpoe = QPushButton("...", self.dlg)
        #self.dlg.bpod = QPushButton("POE_d", self.dlg)
        self.dlg.calcula = QPushButton("Calcular", self.dlg)
        self.dlg.representa = QPushButton("Adicionar", self.dlg)
        #self.dlg.coleta = QPushButton("COLETAR", self.dlg)


        #Conectar Botões às funções
        self.dlg.bproxima.clicked.connect(self.passar_foto)
        self.dlg.banterior.clicked.connect(self.voltar_foto)
        self.dlg.bpoe.clicked.connect(self.ler_arquivo_texto_e)
        #self.dlg.bpod.clicked.connect(self.ler_arquivo_texto_d)
        self.dlg.calcula.clicked.connect(self.stereotriangulation)
        self.dlg.representa.clicked.connect(self.camada)
        #self.dlg.calcula.clicked.connect(self.coletar)


        #Movendo e alterando tamanho de alguns botões
        #self.dlg.bpod.move(0,0)
        self.dlg.bpoe.move(541,47)

        self.dlg.calcula.move(120,580)
        self.dlg.calcula.resize(165,30)

        self.dlg.representa.move(410,700)
        self.dlg.representa.resize(135,30)

        #Setando alguns botões como "inclicaveis" inicialmente
        self.dlg.bproxima.setEnabled(False)
        self.dlg.banterior.setEnabled(False)
        self.dlg.calcula.setEnabled(False)
        self.dlg.representa.setEnabled(False)
        #self.dlg.coleta.setEnabled(False)


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

        #Setando alguns campos como "apenas leitura"
        self.dlg.editPixInfo_d.setReadOnly(True)
        self.dlg.editPixInfo_e.setReadOnly(True)
        self.dlg.plainTextEdit.setReadOnly(True)

        #Agrupando objetos em um mesmo layout (direita e esqueda)
        vertical_e = QWidget(self.dlg)
        vertical_e.setGeometry(QRect(30,90,900,450))
        vertical_e.setObjectName("Camera esquerda")
        HBlayout_e = QHBoxLayout(vertical_e)
        VBlayout_e1 = QVBoxLayout()
        VBlayout_e1.addWidget(self.dlg.visu_e)
        VBlayout_e2 = QVBoxLayout()
        VBlayout_e2.addWidget(self.dlg.bproxima)
        VBlayout_e2.addWidget(self.dlg.banterior)
        #VBlayout_e2.addWidget(self.dlg.coleta)
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
        self.dlg.pixmap_right = 0

        self.filename_right_dir = 0
        self.filename_left_dir = 0

        self.dlg.pxd = 0
        self.dlg.pyd = 0
        self.dlg.pxe = 0
        self.dlg.pye = 0

        self.dlg.vl = 0

        #Distancia focal após estereoretificaçãoptimize (em pixels)
        self.dlg.dfest = 4146.7871579187267

        #Tamanho do pixel em metros
        self.dlg.tamanhop = 0.0000043

        #Base entre câmeras em pixels
        self.dlg.base = 0.67032028/self.dlg.tamanhop

        #Parâmetros WGS84, em metros
        self.dlg.a = 6378137
        self.dlg.b = 6356752.3142
        self.dlg.f = 1/298.257223563
        self.dlg.e2 = 1-(pow(self.dlg.b,2)/pow(self.dlg.a,2))

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

    #A partir daqui todas as funções desenvolvidas para o funcionamento do plugin
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
        self.dlg.visu_d.scale(1.5,1.5)

    def zoomin_e(self):
        self.dlg.visu_e.scale(1.5,1.5)

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
        self.filename_right_dir =  QFileDialog.getExistingDirectory(self.dlg,"Selecionar pasta com imagens camera da direita","/")

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

    #def coletar(self):
        #self.dlg._photo_d.mousePressEvent = self.pixelSelect_d
        #self.dlg._photo_e.mousePressEvent = self.pixelSelect_e

    def handdrag_d(self):
        if self.dlg.visu_d.setDragMode(QGraphicsView.ScrollHandDrag):
            self.dlg.visu_d.setDragMode(QGraphicsView.NoDrag)
        else:
            self.dlg.visu_d.setDragMode(QGraphicsView.ScrollHandDrag)

    def handdrag_e(self):
        if self.dlg.visu_e.setDragMode(QGraphicsView.ScrollHandDrag):
            self.dlg.visu_e.setDragMode(QGraphicsView.NoDrag)
        else:
            self.dlg.visu_e.setDragMode(QGraphicsView.ScrollHandDrag)

    def pixelSelect_d(self,event):
        position_d = QPoint( event.pos().x(),  event.pos().y())
        self.dlg.editPixInfo_d.setText('%d, %d' % (event.pos().x(), event.pos().y()))

        self.dlg.pxd = event.pos().x()
        self.dlg.pyd = event.pos().y()

        self.habilitarbotao()
        #self.handdrag_d()

    def pixelSelect_e(self,event):
        position_e = QPoint( event.pos().x(),  event.pos().y())
        self.dlg.editPixInfo_e.setText('%d, %d' % (event.pos().x(), event.pos().y()))

        self.dlg.pxe = event.pos().x()
        self.dlg.pye = event.pos().y()

        self.habilitarbotao()
        #self.handdrag_e()
        #self.ajustamento_e()

    def habilitarbotao(self):
        if self.dlg.pixmap_left == 0 or self.dlg.pixmap_right == 0:
            self.dlg.bproxima.setEnabled(False)
            self.dlg.banterior.setEnabled(False)
        else:
            self.dlg.bproxima.setEnabled(True)
            self.dlg.banterior.setEnabled(True)

        if self.dlg.pxe == 0 or self.dlg.pxd == 0:
            self.dlg.calcula.setEnabled(False)
        else:
            self.dlg.calcula.setEnabled(True)

        if self.dlg.lineEditFeicao == '' or self.dlg.lineEditDescricao == '' or self.dlg.plainTextEdit == '':
            self.dlg.representa.setEnabled(False)
        else:
            self.dlg.representa.setEnabled(True)

    def ler_arquivo_texto_e(self):
        name = QFileDialog.getOpenFileName(self.dlg,"Selecionar os parametros de orietacao exterior","/")

        texto = []
        reader = csv.reader(open(name), delimiter = ',')
        for row in reader:
            texto.append(row)

        rowCount = len(texto)
        colCount = max([len(p) for p in texto])
        self.dlg.tableWidget_e = QTableWidget()
        self.dlg.tableWidget_e.setRowCount(rowCount)
        self.dlg.tableWidget_e.setColumnCount(colCount)


        for row, foto in enumerate(texto):
            for column, value in enumerate(foto):
                newItem = QTableWidgetItem(value)
                newItem.setFlags(Qt.ItemIsEnabled)
                self.dlg.tableWidget_e.setItem(row, column, newItem)

        self.dlg.lineEdit.setText(name)

    def ler_arquivo_texto_d(self):
        #Atualmente não está sendo usado mas poderá ser usado no futuro
        name = QFileDialog.getOpenFileName(self.dlg,"Selecionar os parametros de orietacao exterior","/")

        texto = []
        reader = csv.reader(open(name), delimiter = ',')
        for row in reader:
            texto.append(row)

        rowCount = len(texto)
        colCount = max([len(p) for p in texto])
        self.dlg.tableWidget_d = QTableWidget()
        self.dlg.tableWidget_d.setRowCount(rowCount)
        self.dlg.tableWidget_d.setColumnCount(colCount)

        for row, foto in enumerate(texto):
            for column, value in enumerate(foto):
                newItem = QTableWidgetItem(value)
                newItem.setFlags(Qt.ItemIsEnabled)
                self.dlg.tableWidget_d.setItem(row, column, newItem)

    def ajustamento_e(self):
        #Não usado no momento, mas poderá ser aproveitado no futuro
        row = self.index

        #Vetor Solução inicial
        si = np.array([0,0,0])

        #POE camera esquerda
        X0e = self.dlg.tableWidget_e.item(row,1).text()
        X0e = float(X0e)
        Y0e = self.dlg.tableWidget_e.item(row,2).text()
        Y0e = float(Y0e)
        Z0e = self.dlg.tableWidget_e.item(row,3).text()
        Z0e = float(Z0e)
        m11e = self.dlg.tableWidget_e.item(row,4).text()
        m11e = float(m11e)
        m12e = self.dlg.tableWidget_e.item(row,5).text()
        m12e = float(m12e)
        m13e = self.dlg.tableWidget_e.item(row,6).text()
        m13e = float(m13e)
        m21e = self.dlg.tableWidget_e.item(row,7).text()
        m21e = float(m21e)
        m22e = self.dlg.tableWidget_e.item(row,8).text()
        m22e = float(m22e)
        m23e = self.dlg.tableWidget_e.item(row,9).text()
        m23e = float(m23e)
        m31e = self.dlg.tableWidget_e.item(row,10).text()
        m31e = float(m31e)
        m32e = self.dlg.tableWidget_e.item(row,11).text()
        m32e = float(m32e)
        m33e = self.dlg.tableWidget_e.item(row,12).text()
        m33e = float(m33e)

        #POE camera direita
        X0d = self.dlg.tableWidget_d.item(row,1).text()
        X0d = float(X0d)
        Y0d = self.dlg.tableWidget_d.item(row,2).text()
        Y0d = float(Y0d)
        Z0d = self.dlg.tableWidget_d.item(row,3).text()
        Z0d = float(Z0d)
        m11d = self.dlg.tableWidget_d.item(row,4).text()
        m11d= float(m11d)
        m12d = self.dlg.tableWidget_d.item(row,5).text()
        m12d= float(m12d)
        m13d = self.dlg.tableWidget_d.item(row,6).text()
        m13d= float(m13d)
        m21d = self.dlg.tableWidget_d.item(row,7).text()
        m21d= float(m21d)
        m22d = self.dlg.tableWidget_d.item(row,8).text()
        m22d= float(m22d)
        m23d = self.dlg.tableWidget_d.item(row,9).text()
        m23d= float(m23d)
        m31d = self.dlg.tableWidget_d.item(row,10).text()
        m31d= float(m31d)
        m32d = self.dlg.tableWidget_d.item(row,11).text()
        m32d= float(m32d)
        m33d = self.dlg.tableWidget_d.item(row,12).text()
        m33d= float(m33d)

        #Valores auxiliares para matriz das derivadas

        Nxe = m11e*(si[0]-X0e) + m12e*(si[1]-Y0e) + m13e*(si[2]-Z0e)
        Nye = m21e*(si[0]-X0e) + m22e*(si[1]-Y0e) + m23e*(si[2]-Z0e)
        De = m31e*(si[0]-X0e) + m32e*(si[1]-Y0e) + m33e*(si[2]-Z0e)

        Nxd = m11d*(si[0]-X0d) + m12d*(si[1]-Y0d) + m13d*(si[2]-Z0d)
        Nyd = m21d*(si[0]-X0d) + m22d*(si[1]-Y0d) + m23d*(si[2]-Z0d)
        Dd = m31d*(si[0]-X0d) + m32d*(si[1]-Y0d) + m33d*(si[2]-Z0d)

        #Matriz derivadas parciais (A)
        A = np.array([[-self.dlg.dfe*((m11e*De-m31e*Nxe)/(pow(De,2))), -self.dlg.dfe*((m12e*De-m32e*Nxe)/(pow(De,2))), -self.dlg.dfe*((m13e*De-m33e*Nxe)/(pow(De,2)))], [-self.dlg.dfe*((m21e*De-m31e*Nye)/(pow(De,2))), -self.dlg.dfe*((m22e*De-m32e*Nye)/(pow(De,2))), -self.dlg.dfe*((m23e*De-m33e*Nye)/(pow(De,2)))], [-self.dlg.dfd*((m11d*Dd-m31d*Nxd)/(pow(Dd,2))), -self.dlg.dfd*((m12d*Dd-m32d*Nxd)/(pow(Dd,2))), -self.dlg.dfd*((m13d*Dd-m33d*Nxd)/(pow(Dd,2)))], [-self.dlg.dfd*((m21d*Dd-m31d*Nyd)/(pow(Dd,2))), -self.dlg.dfd*((m22d*Dd-m32d*Nyd)/(pow(Dd,2))), -self.dlg.dfd*((m23d*Dd-m33d*Nyd)/(pow(Dd,2)))]])

        #Matriz Peso
        P = np.array([[math.sqrt((pow(self.dlg.pxe-self.dlg.ppxe,2))+(pow(self.dlg.pye-self.dlg.ppye,2))), 0, 0, 0], [0, math.sqrt((pow(self.dlg.pxe-self.dlg.ppxe,2))+(pow(self.dlg.pye-self.dlg.ppye,2))), 0, 0], [0, 0, math.sqrt((pow(self.dlg.pxd-self.dlg.ppxd,2))+(pow(self.dlg.pyd-self.dlg.ppyd,2))), 0], [0, 0, 0, math.sqrt((pow(self.dlg.pxd-self.dlg.ppxd,2))+(pow(self.dlg.pyd-self.dlg.ppyd,2)))]])

        P1 = np.array([[10,0,0,0],[0,10,0,0],[0,0,10,0],[0,0,0,10]])

        L0 = np.array([[-self.dlg.dfe*(Nxe/De)+self.dlg.ppxe], [-self.dlg.dfe*(Nye/De)+self.dlg.ppye], [-self.dlg.dfd*(Nxd/Dd)+self.dlg.ppxd], [-self.dlg.dfd*(Nyd/Dd)+self.dlg.ppyd]])

        Lb = np.array([[self.dlg.pxe],[self.dlg.pye],[self.dlg.pxd],[self.dlg.pyd]])

        L = np.subtract(L0,Lb)
        #self.dlg.plainTextEdit.setPlainText(A.shape)

        X = np.matmul(-(pow((np.matmul(np.matmul(A.transpose(),P),A)),-1)),(np.matmul(np.matmul(A.transpose(),P),L)))

        Nxea = m11e*(X[0]-X0e) + m12e*(X[1]-Y0e) + m13e*(X[2]-Z0e)
        Nyea = m21e*(X[0]-X0e) + m22e*(X[1]-Y0e) + m23e*(X[2]-Z0e)
        Dea = m31e*(X[0]-X0e) + m32e*(X[1]-Y0e) + m33e*(X[2]-Z0e)

        Nxda = m11d*(X[0]-X0d) + m12d*(X[1]-Y0d) + m13d*(X[2]-Z0d)
        Nyda = m21d*(X[0]-X0d) + m22d*(X[1]-Y0d) + m23d*(X[2]-Z0d)
        Dda = m31d*(X[0]-X0d) + m32d*(X[1]-Y0d) + m33d*(X[2]-Z0d)

        La = np.array([[-self.dlg.dfe*(Nxea/Dea)+self.dlg.ppxe], [-self.dlg.dfe*(Nyea/Dea)+self.dlg.ppye], [-self.dlg.dfd*(Nxda/Dda)+self.dlg.ppxd], [-self.dlg.dfd*(Nyda/Dda)+self.dlg.ppyd]])

        V = np.subtract(La,Lb)

        varpost = np.matmul(np.matmul(V.transpose(),P1),V)

        luli = np.array2string(X, precision=2, separator=',',suppress_small=True)
        self.dlg.plainTextEdit.setPlainText(luli)

    def stereotriangulation(self):
        row = self.index

        long = self.dlg.tableWidget_e.item(row,1).text()
        long = float(long)
        lat = self.dlg.tableWidget_e.item(row,2).text()
        lat = float(lat)
        alt = self.dlg.tableWidget_e.item(row,3).text()
        alt = float(alt)

        z = (self.dlg.dfest * self.dlg.base)/(self.dlg.pxe - self.dlg.pxd)
        #z em metros
        zm = z * self.dlg.tamanhop

        x = self.dlg.pxe * (z/self.dlg.dfest)
        #x em m
        xm = x * self.dlg.tamanhop

        y = self.dlg.pye * (z/self.dlg.dfest)
        #y em m
        ym = y * self.dlg.tamanhop

        coordpontosimagem = np.array([[xm],[ym],[zm]])

        matrizrotbase = np.array([[float(self.dlg.tableWidget_e.item(row,4).text()),float(self.dlg.tableWidget_e.item(row,5).text()),float(self.dlg.tableWidget_e.item(row,6).text())],[float(self.dlg.tableWidget_e.item(row,7).text()),float(self.dlg.tableWidget_e.item(row,8).text()),float(self.dlg.tableWidget_e.item(row,9).text())],[float(self.dlg.tableWidget_e.item(row,10).text()),float(self.dlg.tableWidget_e.item(row,11).text()),float(self.dlg.tableWidget_e.item(row,12).text())]])

        pontosrefcam = np.matmul(matrizrotbase,coordpontosimagem)

        matrizrotlatlong = np.array([[-math.sin(math.radians(lat)), -math.sin(math.radians(long))*math.cos(math.radians(lat)), math.cos(math.radians(long))*math.cos(math.radians(lat))], [math.cos(math.radians(lat)), -math.sin(math.radians(long))*math.sin(math.radians(lat)), math.cos(math.radians(long))*math.sin(math.radians(lat))], [0, math.cos(math.radians(long)), math.sin(math.radians(long))]])

        wgs84 = pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        geocentric = pyproj.Proj('+proj=geocent +datum=WGS84 +units=m +no_defs')

        lu1,lu2,lu3 = pyproj.transform(wgs84,geocentric,long,lat,alt)

        coordlulicoluna = np.array([[lu1],[lu2],[lu3]])

        pontosrefcartesiana = np.matmul(matrizrotlatlong,pontosrefcam)+coordlulicoluna

        #Transformação das coordenadas cartesianas para as gedésicas
        pontosrefcartesiana1 = pontosrefcartesiana[0]
        pontosrefcartesiana2 = pontosrefcartesiana[1]
        pontosrefcartesiana3 = pontosrefcartesiana[2]
        self.dlg.coordenadas = pyproj.transform(geocentric,wgs84,pontosrefcartesiana1,pontosrefcartesiana2,pontosrefcartesiana3)


        #luli = np.array2string(coordenadas, precision=10, separator=',',suppress_small=True)
        self.dlg.plainTextEdit.setPlainText('')
        self.dlg.plainTextEdit.setPlainText(' Latidude: '+str(self.dlg.coordenadas[1])+'\n Longitude: '+str(self.dlg.coordenadas[0])+'\n Altitude: '+str(self.dlg.coordenadas[2]))

        self.habilitarbotao()

    def camada(self):
        # create layer
        if self.dlg.vl == 0:
            self.dlg.vl = QgsVectorLayer("Point", "Feicoes Temporário", "memory")
            self.dlg.pr = self.dlg.vl.dataProvider()

            # changes are only possible when editing the layer
            self.dlg.vl.startEditing()
            # add fields
            self.dlg.pr.addAttributes([QgsField("Feicao", QVariant.String),QgsField("Descricacao da feicao", QVariant.String)])

            # add layer to the legend
            QgsMapLayerRegistry.instance().addMapLayer(self.dlg.vl)

            # add a feature
            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(self.dlg.coordenadas[0],self.dlg.coordenadas[1])))

            self.dlg.lineEditFeicao.setText('')
            self.dlg.lineEditDescricao.setText('')
            feicao = self.dlg.lineEditFeicao.text()
            descricao = self.dlg.lineEditDescricao.text()

            self.dlg.lineEditFeicao.clear()
            self.dlg.lineEditDescricao.clear()
            self.dlg.plainTextEdit.clear()
            self.dlg.editPixInfo_d.clear()
            self.dlg.editPixInfo_e.clear()

            fet.setAttributes([feicao, descricao])
            self.dlg.pr.addFeatures([fet])

            # commit to stop editing the layer
            self.dlg.vl.commitChanges()

            # update layer's extent when new features have been added
            # because change of extent in provider is not propagated to the layer
            self.dlg.vl.updateExtents()

            self.habilitarbotao()
        else:
            self.dlg.vl.startEditing()

            # add a feature
            fet2 = QgsFeature()
            fet2.setGeometry(QgsGeometry.fromPoint(QgsPoint(self.dlg.coordenadas[0],self.dlg.coordenadas[1])))

            feicao = self.dlg.lineEditFeicao.text()
            descricao = self.dlg.lineEditDescricao.text()

            self.dlg.lineEditFeicao.clear()
            self.dlg.lineEditDescricao.clear()
            self.dlg.plainTextEdit.clear()
            self.dlg.editPixInfo_d.clear()
            self.dlg.editPixInfo_e.clear()

            fet2.setAttributes([feicao, descricao])
            self.dlg.pr.addFeatures([fet2])

            # commit to stop editing the layer
            self.dlg.vl.commitChanges()

            # update layer's extent when new features have been added
            # because change of extent in provider is not propagated to the layer
            self.dlg.vl.updateExtents()

            self.habilitarbotao()

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
