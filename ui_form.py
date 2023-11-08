# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from pyqtgraph import GraphicsView

class Ui_main_window(object):
    def setupUi(self, main_window):
        if not main_window.objectName():
            main_window.setObjectName(u"main_window")
        main_window.resize(884, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(main_window.sizePolicy().hasHeightForWidth())
        main_window.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(u"ecg_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        main_window.setWindowIcon(icon)
        self.gridLayout = QGridLayout(main_window)
        self.gridLayout.setObjectName(u"gridLayout")
        self.ECG_plot = GraphicsView(main_window)
        self.ECG_plot.setObjectName(u"ECG_plot")

        self.gridLayout.addWidget(self.ECG_plot, 1, 0, 1, 1)

        self.control_layout = QHBoxLayout()
        self.control_layout.setObjectName(u"control_layout")
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.control_layout.addItem(self.horizontalSpacer_4)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.title_data_label = QLabel(main_window)
        self.title_data_label.setObjectName(u"title_data_label")

        self.verticalLayout.addWidget(self.title_data_label)

        self.name_label = QLabel(main_window)
        self.name_label.setObjectName(u"name_label")

        self.verticalLayout.addWidget(self.name_label)

        self.name_line = QLineEdit(main_window)
        self.name_line.setObjectName(u"name_line")

        self.verticalLayout.addWidget(self.name_line)

        self.age_label = QLabel(main_window)
        self.age_label.setObjectName(u"age_label")

        self.verticalLayout.addWidget(self.age_label)

        self.age_line = QLineEdit(main_window)
        self.age_line.setObjectName(u"age_line")

        self.verticalLayout.addWidget(self.age_line)

        self.sex_label = QLabel(main_window)
        self.sex_label.setObjectName(u"sex_label")

        self.verticalLayout.addWidget(self.sex_label)

        self.sex_box = QComboBox(main_window)
        self.sex_box.addItem("")
        self.sex_box.addItem("")
        self.sex_box.addItem("")
        self.sex_box.setObjectName(u"sex_box")

        self.verticalLayout.addWidget(self.sex_box)


        self.control_layout.addLayout(self.verticalLayout)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.control_layout.addItem(self.horizontalSpacer)

        self.communication_layout = QVBoxLayout()
        self.communication_layout.setObjectName(u"communication_layout")
        self.connect_button = QPushButton(main_window)
        self.connect_button.setObjectName(u"connect_button")

        self.communication_layout.addWidget(self.connect_button)

        self.toggle_recording_button = QPushButton(main_window)
        self.toggle_recording_button.setObjectName(u"toggle_recording_button")

        self.communication_layout.addWidget(self.toggle_recording_button)


        self.control_layout.addLayout(self.communication_layout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.control_layout.addItem(self.horizontalSpacer_2)

        self.filter_layout = QVBoxLayout()
        self.filter_layout.setObjectName(u"filter_layout")
        self.title = QLabel(main_window)
        self.title.setObjectName(u"title")

        self.filter_layout.addWidget(self.title)

        self.noise_line_remover = QCheckBox(main_window)
        self.noise_line_remover.setObjectName(u"noise_line_remover")

        self.filter_layout.addWidget(self.noise_line_remover)

        self.line_frequency_layout = QHBoxLayout()
        self.line_frequency_layout.setObjectName(u"line_frequency_layout")
        self.frequency_descriptor = QLabel(main_window)
        self.frequency_descriptor.setObjectName(u"frequency_descriptor")

        self.line_frequency_layout.addWidget(self.frequency_descriptor)

        self.comboBox = QComboBox(main_window)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")

        self.line_frequency_layout.addWidget(self.comboBox)


        self.filter_layout.addLayout(self.line_frequency_layout)

        self.passband_filter = QCheckBox(main_window)
        self.passband_filter.setObjectName(u"passband_filter")

        self.filter_layout.addWidget(self.passband_filter)


        self.control_layout.addLayout(self.filter_layout)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.control_layout.addItem(self.horizontalSpacer_3)


        self.gridLayout.addLayout(self.control_layout, 0, 0, 1, 1)


        self.retranslateUi(main_window)

        QMetaObject.connectSlotsByName(main_window)
    # setupUi

    def retranslateUi(self, main_window):
        main_window.setWindowTitle(QCoreApplication.translate("main_window", u"ECG Recording", None))
        self.title_data_label.setText(QCoreApplication.translate("main_window", u"Patient's information", None))
        self.name_label.setText(QCoreApplication.translate("main_window", u"Full Name", None))
        self.age_label.setText(QCoreApplication.translate("main_window", u"Age", None))
        self.sex_label.setText(QCoreApplication.translate("main_window", u"Sex", None))
        self.sex_box.setItemText(0, QCoreApplication.translate("main_window", u"Select", None))
        self.sex_box.setItemText(1, QCoreApplication.translate("main_window", u"Man", None))
        self.sex_box.setItemText(2, QCoreApplication.translate("main_window", u"Woman", None))

        self.connect_button.setText(QCoreApplication.translate("main_window", u"Connect Arduino", None))
        self.toggle_recording_button.setText(QCoreApplication.translate("main_window", u"Start Recording", None))
        self.title.setText(QCoreApplication.translate("main_window", u"Filters", None))
        self.noise_line_remover.setText(QCoreApplication.translate("main_window", u"Line Noise Removal", None))
        self.frequency_descriptor.setText(QCoreApplication.translate("main_window", u"Frequency", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("main_window", u"50Hz", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("main_window", u"60Hz", None))

        self.passband_filter.setText(QCoreApplication.translate("main_window", u"Pass-Band Filter", None))
    # retranslateUi

