# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from pathlib import Path
from importlib.resources import files

from PySide6.QtCore import QSettings, QFile, QTextStream
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6 import QtWidgets
from PySide6.QtUiTools import loadUiType

from steel_connections.gui.toggle_button import Switch

from steel_connections.bfp_connection import BFPConnection
from steel_connections.member.member import SteelSection
from steel_connections.component.bolt import Bolt, BoltGroup2D
from steel_connections.component.plate import Plate



# Load UI class
current_path = Path(__file__).parent
ui_path = current_path / 'gui' / 'widgets' / 'main_window.ui'
UI_Class, Base_Class = loadUiType(str(ui_path))


class MainWindow(Base_Class, UI_Class):
    def __init__(self):
        super().__init__()
        
        # Setup UI - this makes all widgets available as self.widget_name
        self.setupUi(self)
        self.add_theme_switch()
        self.fill_thickness()
        self.create_connections()
        self.load_settings()

    def add_theme_switch(self):
        self.switch = Switch(self.centralwidget, thumb_radius=8, track_radius=6)
        self.centralwidget.layout().addWidget(self.switch)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.switch.setSizePolicy(sizePolicy)

    def fill_thickness(self):
        thicknesses = [str(t) for t in Plate.standard_thickness]
        self.plate_thickness.addItems(thicknesses)
        self.beam_tf.addItems(thicknesses)
        self.beam_tw.addItems(thicknesses)
        self.column_tf.addItems(thicknesses)
        self.column_tw.addItems(thicknesses)


    def closeEvent(self, event):
        qsettings = QSettings("steel_connection", "main_window")
        qsettings.setValue("geometry", self.saveGeometry())
        qsettings.setValue("saveState", self.saveState())
        qsettings.setValue("pos", self.pos())
        qsettings.setValue("size", self.size())
        super().closeEvent(event)

    def load_settings(self):
        qsettings = QSettings("steel_connection", "main_window")
        self.restoreGeometry(qsettings.value("geometry", self.saveGeometry()))
        self.restoreState(qsettings.value("saveState", self.saveState()))
        self.move(qsettings.value("pos", self.pos()))
        self.resize(qsettings.value("size", self.size()))

    def create_connections(self):
        # spin boxes and value changes
        self.beam_bf.valueChanged.connect(self.calculate_connection)
        self.beam_totaldepth.valueChanged.connect(self.calculate_connection)
        self.column_bf.valueChanged.connect(self.calculate_connection)
        self.column_totaldepth.valueChanged.connect(self.calculate_connection)
        self.plate_width.valueChanged.connect(self.calculate_connection)
        self.plate_length.valueChanged.connect(self.calculate_connection)
        self.plate_length.valueChanged.connect(self.calculate_connection)
        self.bolt_n.valueChanged.connect(self.calculate_connection)
        self.bolt_m.valueChanged.connect(self.calculate_connection)
        # combo boxes and index changes
        self.beam_tf.currentIndexChanged.connect(self.calculate_connection)
        self.beam_tw.currentIndexChanged.connect(self.calculate_connection)
        self.column_tf.currentIndexChanged.connect(self.calculate_connection)
        self.column_tw.currentIndexChanged.connect(self.calculate_connection)
        self.plate_thickness.currentIndexChanged.connect(self.calculate_connection)
        self.bolt_diameter.currentIndexChanged.connect(self.calculate_connection)
        # theme switch
        self.switch.toggled.connect(self.change_theme)

    def calculate_connection(self):
        try:
            section_dict_beam={
                    'sec_type': 'WB',
                    'b': self.beam_bf.value(),
                    'd': self.beam_totaldepth.value(),
                    't_w': float(self.beam_tw.currentText()),
                    't_f': float(self.beam_tf.currentText()),
                    't': float(self.beam_tf.currentText()),
                    'f_y': 2400,
                    'f_yw': 2400,
                    'f_u': 3700,
            }
            section_dict_column={
                    'sec_type': 'WC',
                    'b': self.column_bf.value(),
                    'd': self.column_totaldepth.value(),
                    't_w': float(self.column_tw.currentText()),
                    't_f': float(self.column_tf.currentText()),
                    't': float(self.column_tf.currentText()),
                    'f_y': 2400,
                    'f_yw': 2400,
                    'f_u': 3700,
            }
            beam = SteelSection.from_section_dict(section_dict_beam)
            col = SteelSection.from_section_dict(section_dict_column)
            bolt_diameter = float(self.bolt_diameter.currentText())
            n_bolts = int(self.bolt_n.value())
            m_bolts = int(self.bolt_m.value())
            bolt = Bolt(d_f=bolt_diameter)
            bolt_group = BoltGroup2D(n_p=n_bolts, n_g=m_bolts, bolt=bolt, s_p=8.4, s_g=5)
            plate = Plate(
                b_i=self.plate_width.value(),
                h_i=self.plate_length.value(),
                t_i=float(self.plate_thickness.currentText())
            )
            connection = BFPConnection(
                beam=beam,
                column=col,
                plate=plate,
                bolt_group=bolt_group,
                s1=7,
                beam_length=755,
            )
            errors = connection.check_connection()
            self.results.clear()
            self.log_info("Connection Results:")
            if len(errors) == 0:
                self.log_success("The connection is adequate.")
            else:
                self.log_error("The connection is NOT adequate:")
                for error in errors:
                    self.log_warning(f"- {error.description}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during calculation: {e}")
          
    def log_success(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results.append(
            f"[{timestamp}] <span style='color: green; font-weight: bold;'>✓ SUCCESS:</span> {message}"
        )
    
    def log_error(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results.append(
            f"[{timestamp}] <span style='color: red; font-weight: bold;'>✗ ERROR:</span> {message}"
        )
    
    def log_warning(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results.append(
            f"[{timestamp}] <span style='color: orange; font-weight: bold;'>⚠ WARNING:</span> {message}"
        )
    
    def log_info(self, message, color="#000000"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results.append(
            f"[{timestamp}] <span style='color: {color};'>ℹ INFO:</span> {message}"
        )

    def change_theme(self):
        state = self.switch.isChecked()
        toggle_stylesheet(state)


def toggle_stylesheet(state):
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("No Qt Application found.")
    if state:
        path = 'darkstyle.qss'
    else:
        path = 'light.qss'
    theme_path = str(files("steel_connections.data.themes").joinpath(path))
    file = QFile(theme_path)
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())


def main():
    app = QApplication(sys.argv)
    # translator = QtCore.QTranslator()
    # translator.load("applications/section/mainwindow.qm")
    # app.installTranslator(translator)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
