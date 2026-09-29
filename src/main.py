import sys
import os
import json
import copy

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QInputDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QGroupBox,
    QHeaderView,
    QFrame,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
)

from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QBrush, QColor, QFont

from PySide6.QtCore import Qt, Signal, QPoint

import pandas as pd

# ============================================================
# GRAPH WIDGET
# ============================================================


class GraphWidget(QWidget):

    mouse_clicked = Signal(float, float)
    point_selected = Signal(int)

    def __init__(self):
        super().__init__()

        self.image = QPixmap()
        self.points = []
        self.selected_point_index = None

        self.zoom_factor = 1.0
        self.zoom_center_x = 0.5
        self.zoom_center_y = 0.5

        self.hand_mode = False
        self.panning = False
        self.pan_start = QPoint()

        # Point selection mode
        self.point_selection_mode = False

        self.setMinimumSize(700, 500)
        self.setMouseTracking(True)

    def set_point_selection_mode(self, enabled):
        self.point_selection_mode = bool(enabled)

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    def set_image(self, pixmap):

        self.image = pixmap
        self.points = []
        self.selected_point_index = None

        self.zoom_factor = 1.0
        self.zoom_center_x = 0.5
        self.zoom_center_y = 0.5

        self.update()

    def clear_points(self):

        self.points = []
        self.selected_point_index = None

        self.update()

    # --------------------------------------------------------
    # DISPLAY PARAMETERS
    # --------------------------------------------------------

    def get_display_parameters(self):

        if self.image.isNull():
            return 0, 0, 1, 1

        image_width = self.image.width()
        image_height = self.image.height()

        widget_width = self.width()
        widget_height = self.height()

        if image_width <= 0 or image_height <= 0:
            return 0, 0, 1, 1

        scale_x = widget_width / image_width
        scale_y = widget_height / image_height

        base_scale = min(scale_x, scale_y)

        scale = base_scale * self.zoom_factor

        display_width = image_width * scale
        display_height = image_height * scale

        if self.zoom_factor <= 1.0:

            offset_x = (widget_width - display_width) / 2

            offset_y = (widget_height - display_height) / 2

        else:

            center_pixel_x = self.zoom_center_x * image_width

            center_pixel_y = self.zoom_center_y * image_height

            offset_x = widget_width / 2 - center_pixel_x * scale

            offset_y = widget_height / 2 - center_pixel_y * scale

        return (offset_x, offset_y, scale, scale)

    # --------------------------------------------------------
    # ZOOM
    # --------------------------------------------------------

    def zoom_in(self):

        self.zoom_factor *= 1.25

        if self.zoom_factor > 8.0:
            self.zoom_factor = 8.0

        self.update()

    def zoom_out(self):

        self.zoom_factor /= 1.25

        if self.zoom_factor < 1.0:
            self.zoom_factor = 1.0

        self.update()

    def reset_zoom(self):

        self.zoom_factor = 1.0
        self.zoom_center_x = 0.5
        self.zoom_center_y = 0.5

        self.update()

    def zoom_at(self, widget_x, widget_y, factor):

        if self.image.isNull():
            return

        image_x, image_y = self.widget_to_image(widget_x, widget_y)

        old_zoom = self.zoom_factor

        self.zoom_factor *= factor

        if self.zoom_factor < 1.0:
            self.zoom_factor = 1.0

        if self.zoom_factor > 8.0:
            self.zoom_factor = 8.0

        if old_zoom != self.zoom_factor:

            image_width = self.image.width()
            image_height = self.image.height()

            if image_width > 0 and image_height > 0:

                self.zoom_center_x = image_x / image_width

                self.zoom_center_y = image_y / image_height

        self.update()

    # --------------------------------------------------------
    # COORDINATE CONVERSION
    # --------------------------------------------------------

    def widget_to_image(self, widget_x, widget_y):

        offset_x, offset_y, scale_x, scale_y = self.get_display_parameters()

        if scale_x == 0 or scale_y == 0:
            return 0, 0

        image_x = (widget_x - offset_x) / scale_x

        image_y = (widget_y - offset_y) / scale_y

        return (image_x, image_y)

    def image_to_widget(self, image_x, image_y):

        offset_x, offset_y, scale_x, scale_y = self.get_display_parameters()

        widget_x = offset_x + image_x * scale_x

        widget_y = offset_y + image_y * scale_y

        return (widget_x, widget_y)

    # --------------------------------------------------------
    # PAINT
    # --------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor(235, 235, 235))

        if self.image.isNull():

            painter.setPen(QColor(100, 100, 100))

            painter.drawText(self.rect(), Qt.AlignCenter, "No graph image loaded")

            return

        offset_x, offset_y, scale_x, scale_y = self.get_display_parameters()

        target_rect = self.image.rect()

        target_rect = target_rect.translated(int(offset_x), int(offset_y))

        target_rect.setWidth(int(self.image.width() * scale_x))

        target_rect.setHeight(int(self.image.height() * scale_y))

        painter.drawPixmap(target_rect, self.image)

        # ----------------------------------------------------
        # DRAW POINTS
        # ----------------------------------------------------

        for index, point in enumerate(self.points):

            pixel_x = point.get("pixel_x", 0)

            pixel_y = point.get("pixel_y", 0)

            widget_x, widget_y = self.image_to_widget(pixel_x, pixel_y)

            if index == self.selected_point_index:

                painter.setPen(QPen(QColor(0, 70, 220), 3))

                painter.setBrush(QBrush(QColor(120, 220, 255)))

                radius = 9

            else:

                painter.setPen(QPen(QColor(220, 0, 0), 2))

                painter.setBrush(QBrush(QColor(255, 220, 0)))

                radius = 6

            painter.drawEllipse(
                int(widget_x - radius), int(widget_y - radius), radius * 2, radius * 2
            )

            painter.setPen(QPen(QColor(0, 0, 0), 2))

            painter.setFont(QFont("Arial", 10, QFont.Bold))

            painter.drawText(int(widget_x + 8), int(widget_y - 8), str(index + 1))

    # --------------------------------------------------------
    # MOUSE WHEEL
    # --------------------------------------------------------

    def wheelEvent(self, event):

        if self.image.isNull():
            return

        position = event.position()

        if event.angleDelta().y() > 0:

            self.zoom_at(position.x(), position.y(), 1.15)

        else:

            self.zoom_at(position.x(), position.y(), 1 / 1.15)

    # --------------------------------------------------------
    # MOUSE PRESS
    # --------------------------------------------------------

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            # ------------------------------------------------
            # HAND / PAN MODE
            # ------------------------------------------------

            if self.hand_mode and self.zoom_factor > 1.0:

                self.panning = True

                self.pan_start = event.position().toPoint()

                self.setCursor(Qt.ClosedHandCursor)

                event.accept()
                return

            # ------------------------------------------------
            # CONVERT WIDGET POSITION TO IMAGE POSITION
            # ------------------------------------------------

            widget_x = event.position().x()
            widget_y = event.position().y()

            image_x, image_y = self.widget_to_image(widget_x, widget_y)

            # ------------------------------------------------
            # SAFETY CHECK
            # Ignore clicks outside the actual image.
            # ------------------------------------------------

            if self.image.isNull():

                event.accept()
                return

            if (
                image_x < 0
                or image_y < 0
                or image_x > self.image.width()
                or image_y > self.image.height()
            ):

                event.accept()
                return

            # ------------------------------------------------
            # EXISTING POINT SELECTION
            # Only active when Point Selection Mode is ON.
            # ------------------------------------------------

            if self.point_selection_mode:

                nearest_index = self.find_nearest_point(image_x, image_y)

                if nearest_index is not None:

                    # Existing point selected
                    self.selected_point_index = nearest_index

                    self.point_selected.emit(nearest_index)

                    self.update()

                    event.accept()
                    return

            # ------------------------------------------------
            # NEW POINT LOCATION
            # ------------------------------------------------

            self.mouse_clicked.emit(image_x, image_y)

            event.accept()
            return

        super().mousePressEvent(event)

    # --------------------------------------------------------
    # FIND NEAREST POINT
    # --------------------------------------------------------

    def find_nearest_point(self, image_x, image_y):

        if not self.points:
            return None

        _, _, scale_x, scale_y = self.get_display_parameters()

        scale = max(min(scale_x, scale_y), 0.0001)

        tolerance_image = 12.0 / scale

        nearest_index = None
        nearest_distance = None

        for index, point in enumerate(self.points):

            px = float(point.get("pixel_x", 0))

            py = float(point.get("pixel_y", 0))

            distance = ((image_x - px) ** 2 + (image_y - py) ** 2) ** 0.5

            if distance <= tolerance_image:

                if nearest_distance is None or distance < nearest_distance:

                    nearest_distance = distance
                    nearest_index = index

        return nearest_index

    # --------------------------------------------------------
    # MOUSE MOVE
    # --------------------------------------------------------

    def mouseMoveEvent(self, event):

        if self.panning:

            current = event.position().toPoint()

            dx = current.x() - self.pan_start.x()

            dy = current.y() - self.pan_start.y()

            _, _, scale_x, scale_y = self.get_display_parameters()

            if scale_x != 0:

                self.zoom_center_x -= dx / (self.image.width() * scale_x)

            if scale_y != 0:

                self.zoom_center_y -= dy / (self.image.height() * scale_y)

            self.zoom_center_x = max(0.0, min(1.0, self.zoom_center_x))

            self.zoom_center_y = max(0.0, min(1.0, self.zoom_center_y))

            self.pan_start = current

            self.update()

            event.accept()
            return

        super().mouseMoveEvent(event)

    # --------------------------------------------------------
    # MOUSE RELEASE
    # --------------------------------------------------------

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:

            if self.panning:

                self.panning = False

                if self.hand_mode:

                    self.setCursor(Qt.OpenHandCursor)

                else:

                    self.setCursor(Qt.ArrowCursor)

                event.accept()
                return

        super().mouseReleaseEvent(event)


# ============================================================
# MAIN APPLICATION
# ============================================================


class PumpCurveApp(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("PumpCurvX - Pump Performance Curve Data Extractor")

        self.resize(1400, 900)

        # ----------------------------------------------------
        # CALIBRATION DATA
        # ----------------------------------------------------

        self.x_min_pixel = None
        self.x_max_pixel = None
        self.y_min_pixel = None
        self.y_max_pixel = None

        self.calibration_mode = None

        # ----------------------------------------------------
        # CURVE DATA
        # ----------------------------------------------------

        self.head_curve_points = []
        self.efficiency_curve_points = []

        self.curves = [
            {
                "name": "Head vs Flow - 1480 RPM",
                "type": "Head vs Flow",
                "rpm": 1480,
                "points": self.head_curve_points,
            },
            {
                "name": "Efficiency vs Flow - 1480 RPM",
                "type": "Efficiency vs Flow",
                "rpm": 1480,
                "points": self.efficiency_curve_points,
            },
        ]

        self.active_curve_index = 0

        self.selected_point_index = None

        self.undo_history = {}

        # ----------------------------------------------------
        # IMAGE / PROJECT
        # ----------------------------------------------------

        self.graph_image = QPixmap()

        self.current_project_path = None

        # ----------------------------------------------------
        # BUILD UI
        # ----------------------------------------------------

        self.build_ui()

    def show_about(self):

        about = QDialog(self)

        about.setWindowTitle("About PumpCurvX")

        about.setFixedSize(520, 470)

        # ====================================================
        # MAIN LAYOUT
        # ====================================================

        layout = QVBoxLayout(about)

        layout.setContentsMargins(30, 25, 30, 25)

        layout.setSpacing(8)

        # ====================================================
        # LOGO
        # ====================================================

        logo_label = QLabel()

        logo_label.setAlignment(Qt.AlignCenter)

        if os.path.exists("PumpCurvX.ico"):

            pixmap = QPixmap("PumpCurvX.ico")

            logo_label.setPixmap(
                pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        layout.addWidget(logo_label)

        # ====================================================
        # PRODUCT NAME
        # ====================================================

        name_label = QLabel("PumpCurvX")

        name_label.setAlignment(Qt.AlignCenter)

        name_label.setFont(QFont("Arial", 24, QFont.Bold))

        name_label.setStyleSheet("color: #1f2937;")

        layout.addWidget(name_label)

        # ====================================================
        # PRODUCT DESCRIPTION
        # ====================================================

        desc_label = QLabel("Pump Performance Curve Data Extractor")

        desc_label.setAlignment(Qt.AlignCenter)

        desc_label.setFont(QFont("Arial", 12, QFont.Bold))

        desc_label.setStyleSheet("color: #4b5563;")

        layout.addWidget(desc_label)

        # ====================================================
        # VERSION
        # ====================================================

        version_label = QLabel("Version 1.5.1")

        version_label.setAlignment(Qt.AlignCenter)

        version_label.setFont(QFont("Arial", 10, QFont.Bold))

        version_label.setStyleSheet("color: #6b7280;")

        layout.addWidget(version_label)

        # ====================================================
        # SEPARATOR
        # ====================================================

        line = QFrame()

        line.setFrameShape(QFrame.HLine)

        line.setFrameShadow(QFrame.Sunken)

        layout.addSpacing(8)

        layout.addWidget(line)

        # ====================================================
        # APPLICATION DESCRIPTION
        # ====================================================

        info_label = QLabel(
            "PumpCurvX is a desktop engineering application "
            "for extracting pump performance curve data from "
            "graphical pump curve images and preparing "
            "structured engineering data for analysis and "
            "reporting."
        )

        info_label.setWordWrap(True)

        info_label.setAlignment(Qt.AlignCenter)

        info_label.setFont(QFont("Arial", 10))

        info_label.setStyleSheet("color: #374151;")

        layout.addSpacing(8)

        layout.addWidget(info_label)

        # ====================================================
        # KEY FEATURES
        # ====================================================

        features_title = QLabel("Key Features")

        features_title.setAlignment(Qt.AlignCenter)

        features_title.setFont(QFont("Arial", 11, QFont.Bold))

        features_title.setStyleSheet("color: #1f2937;")

        layout.addSpacing(8)

        layout.addWidget(features_title)

        features_label = QLabel(
            "• Pump curve image import\n"
            "• Axis calibration\n"
            "• Curve point extraction\n"
            "• Multiple curve management\n"
            "• Data editing and validation\n"
            "• Excel data export"
        )

        features_label.setAlignment(Qt.AlignCenter)

        features_label.setFont(QFont("Arial", 9))

        features_label.setStyleSheet("color: #4b5563;")

        layout.addWidget(features_label)

        # ====================================================
        # COPYRIGHT
        # ====================================================

        copyright_label = QLabel("© 2026 PumpCurvX")

        copyright_label.setAlignment(Qt.AlignCenter)

        copyright_label.setFont(QFont("Arial", 9))

        copyright_label.setStyleSheet("color: #6b7280;")

        layout.addSpacing(10)

        layout.addWidget(copyright_label)

        # ====================================================
        # OK BUTTON
        # ====================================================

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)

        buttons.setStyleSheet("""
            QPushButton {
                min-width: 80px;
                padding: 6px 14px;
                font-weight: bold;
            }
            """)

        buttons.accepted.connect(about.accept)

        layout.addSpacing(5)

        layout.addWidget(buttons, alignment=Qt.AlignCenter)

        # ====================================================
        # SHOW DIALOG
        # ====================================================

        about.exec()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        main_layout.setContentsMargins(10, 8, 10, 8)

        main_layout.setSpacing(6)

        # ====================================================
        # HEADER
        # ====================================================

        header_frame = QFrame()

        header_frame.setFrameShape(QFrame.StyledPanel)

        header_layout = QHBoxLayout(header_frame)

        header_layout.setContentsMargins(10, 5, 10, 5)

        title_label = QLabel("PUMP PERFORMANCE CURVE DATA EXTRACTOR")

        title_label.setFont(QFont("Arial", 16, QFont.Bold))

        title_label.setStyleSheet("color: #1f2937;")

        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # ====================================================
        # ABOUT BUTTON
        # ====================================================

        about_button = QPushButton("About")

        about_button.setFixedSize(70, 28)

        about_button.setFont(QFont("Arial", 9, QFont.Bold))

        about_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #777777;
                border-radius: 4px;
                background-color: #eeeeee;
                color: #333333;
                padding: 2px;
            }

            QPushButton:hover {
                background-color: #dddddd;
            }

            QPushButton:pressed {
                background-color: #cccccc;
            }
            """)

        about_button.clicked.connect(self.show_about)

        header_layout.addWidget(about_button)

        # ====================================================
        # ADS LABEL
        # ====================================================

        ads_label = QLabel("ads")

        ads_label.setFont(QFont("Arial", 9, QFont.Bold))

        ads_label.setAlignment(Qt.AlignCenter)

        ads_label.setFixedSize(32, 24)

        ads_label.setStyleSheet("""
            QLabel {
                border: 1px solid #777777;
                border-radius: 4px;
                background-color: #eeeeee;
                color: #444444;
                padding: 2px;
            }
            """)

        header_layout.addWidget(ads_label)

        main_layout.addWidget(header_frame)

        # ====================================================
        # PUMP INFORMATION
        # ====================================================

        pump_info_group = QGroupBox("Pump Information")

        pump_info_layout = QGridLayout(pump_info_group)

        pump_info_layout.setContentsMargins(8, 5, 8, 5)

        pump_info_layout.setHorizontalSpacing(8)

        pump_info_layout.setVerticalSpacing(4)

        pump_info_layout.addWidget(QLabel("Pump Name:"), 0, 0)

        self.pump_name_input = QLineEdit()

        self.pump_name_input.setPlaceholderText("Enter pump name")

        pump_info_layout.addWidget(self.pump_name_input, 0, 1)

        pump_info_layout.addWidget(QLabel("Manufacturer:"), 0, 2)

        self.manufacturer_input = QLineEdit()

        self.manufacturer_input.setPlaceholderText("Enter manufacturer")

        pump_info_layout.addWidget(self.manufacturer_input, 0, 3)

        pump_info_layout.addWidget(QLabel("Model:"), 0, 4)

        self.model_input = QLineEdit()

        self.model_input.setPlaceholderText("Enter model")

        pump_info_layout.addWidget(self.model_input, 0, 5)

        pump_info_layout.addWidget(QLabel("Pump Type:"), 1, 0)

        self.pump_type_input = QLineEdit()

        self.pump_type_input.setPlaceholderText(
            "Centrifugal / Positive Displacement etc."
        )

        pump_info_layout.addWidget(self.pump_type_input, 1, 1)

        pump_info_layout.addWidget(QLabel("Fluid:"), 1, 2)

        self.fluid_input = QLineEdit()

        self.fluid_input.setPlaceholderText("Enter fluid")

        pump_info_layout.addWidget(self.fluid_input, 1, 3)

        pump_info_layout.addWidget(QLabel("Remarks:"), 1, 4)

        self.remarks_input = QLineEdit()

        self.remarks_input.setPlaceholderText("Enter remarks")

        pump_info_layout.addWidget(self.remarks_input, 1, 5)

        for column in [1, 3, 5]:

            pump_info_layout.setColumnStretch(column, 1)

        main_layout.addWidget(pump_info_group)

        # ====================================================
        # FILE CONTROLS
        # ====================================================

        file_group = QGroupBox("1. Graph / Project")

        file_layout = QHBoxLayout(file_group)

        self.open_image_button = QPushButton("Open Graph Image")

        self.save_project_button = QPushButton("Save Project")

        self.open_project_button = QPushButton("Open Project")

        self.paste_image_button = QPushButton("Paste Screenshot")

        self.clear_image_button = QPushButton("Clear Image")

        file_layout.addWidget(self.open_image_button)

        file_layout.addWidget(self.save_project_button)

        file_layout.addWidget(self.open_project_button)

        file_layout.addWidget(self.paste_image_button)

        file_layout.addWidget(self.clear_image_button)

        main_layout.addWidget(file_group)

        # ====================================================
        # CURVE MANAGER
        # ====================================================

        curve_manager_group = QGroupBox("Curve Manager")

        curve_manager_layout = QVBoxLayout()

        curve_select_layout = QHBoxLayout()

        curve_select_layout.addWidget(QLabel("Curve:"))

        self.curve_selector = QComboBox()

        curve_select_layout.addWidget(self.curve_selector)

        curve_manager_layout.addLayout(curve_select_layout)

        curve_button_layout = QHBoxLayout()

        self.add_curve_button = QPushButton("+ Add Curve")

        self.rename_curve_button = QPushButton("Rename")

        self.duplicate_curve_button = QPushButton("Duplicate")

        self.delete_curve_button = QPushButton("Delete")

        curve_button_layout.addWidget(self.add_curve_button)

        curve_button_layout.addWidget(self.rename_curve_button)

        curve_button_layout.addWidget(self.duplicate_curve_button)

        curve_button_layout.addWidget(self.delete_curve_button)

        curve_manager_layout.addLayout(curve_button_layout)

        curve_property_layout = QHBoxLayout()

        curve_property_layout.addWidget(QLabel("Curve Type:"))

        self.curve_type_input = QComboBox()

        self.curve_type_input.addItems(["Head vs Flow", "Efficiency vs Flow"])

        curve_property_layout.addWidget(self.curve_type_input)

        curve_property_layout.addWidget(QLabel("RPM:"))

        self.rpm_input = QSpinBox()

        self.rpm_input.setRange(1, 100000)

        self.rpm_input.setValue(1480)

        curve_property_layout.addWidget(self.rpm_input)

        curve_manager_layout.addLayout(curve_property_layout)

        curve_manager_group.setLayout(curve_manager_layout)

        main_layout.addWidget(curve_manager_group)

        # ====================================================
        # CALIBRATION
        # ====================================================

        calibration_group = QGroupBox("3. Axis Calibration")

        calibration_layout = QGridLayout(calibration_group)

        calibration_layout.setContentsMargins(8, 5, 8, 5)

        calibration_layout.addWidget(QLabel("X Min:"), 0, 0)

        self.x_min_input = QLineEdit()

        self.x_min_input.setPlaceholderText("Engineering value")

        calibration_layout.addWidget(self.x_min_input, 0, 1)

        self.x_min_button = QPushButton("Select X Min Pixel")

        calibration_layout.addWidget(self.x_min_button, 0, 2)

        calibration_layout.addWidget(QLabel("X Max:"), 0, 3)

        self.x_max_input = QLineEdit()

        self.x_max_input.setPlaceholderText("Engineering value")

        calibration_layout.addWidget(self.x_max_input, 0, 4)

        self.x_max_button = QPushButton("Select X Max Pixel")

        calibration_layout.addWidget(self.x_max_button, 0, 5)

        calibration_layout.addWidget(QLabel("Y Min:"), 1, 0)

        self.y_min_input = QLineEdit()

        self.y_min_input.setPlaceholderText("Engineering value")

        calibration_layout.addWidget(self.y_min_input, 1, 1)

        self.y_min_button = QPushButton("Select Y Min Pixel")

        calibration_layout.addWidget(self.y_min_button, 1, 2)

        calibration_layout.addWidget(QLabel("Y Max:"), 1, 3)

        self.y_max_input = QLineEdit()

        self.y_max_input.setPlaceholderText("Engineering value")

        calibration_layout.addWidget(self.y_max_input, 1, 4)

        self.y_max_button = QPushButton("Select Y Max Pixel")

        calibration_layout.addWidget(self.y_max_button, 1, 5)

        self.calibration_status = QLabel("Calibration not completed")

        self.calibration_status.setStyleSheet("color: #b00020;")

        calibration_layout.addWidget(self.calibration_status, 2, 0, 1, 4)

        self.clear_calibration_button = QPushButton("Clear Calibration")

        calibration_layout.addWidget(self.clear_calibration_button, 2, 4, 1, 2)

        main_layout.addWidget(calibration_group)

        # ====================================================
        # GRAPH
        # ====================================================

        self.graph = GraphWidget()

        main_layout.addWidget(self.graph, 1)

        # ====================================================
        # ZOOM CONTROLS
        # ====================================================

        zoom_layout = QHBoxLayout()

        self.zoom_in_button = QPushButton("Zoom In")

        self.zoom_out_button = QPushButton("Zoom Out")

        self.reset_zoom_button = QPushButton("Reset Zoom")

        self.hand_button = QPushButton("Hand / Pan")

        self.hand_button.setCheckable(True)

        self.zoom_status = QLabel("Zoom: 100%")

        zoom_layout.addWidget(self.zoom_in_button)

        zoom_layout.addWidget(self.zoom_out_button)

        zoom_layout.addWidget(self.reset_zoom_button)

        zoom_layout.addWidget(self.hand_button)

        zoom_layout.addWidget(self.zoom_status)

        zoom_layout.addStretch()

        main_layout.addLayout(zoom_layout)

        # ====================================================
        # POINT CONTROLS
        # ====================================================

        point_group = QGroupBox("4. Curve Point Selection")

        point_layout = QHBoxLayout(point_group)

        self.select_points_button = QPushButton("Select Curve Points")

        self.select_points_button.setCheckable(True)

        self.delete_last_button = QPushButton("Delete Last Point")

        self.delete_selected_button = QPushButton("Delete Selected Point")

        self.edit_selected_button = QPushButton("Edit Selected Point")

        self.undo_button = QPushButton("Undo Last Point")

        self.clear_points_button = QPushButton("Clear Current Curve Points")

        self.export_excel_button = QPushButton("Export to Excel")

        point_layout.addWidget(self.select_points_button)

        point_layout.addWidget(self.delete_last_button)

        point_layout.addWidget(self.delete_selected_button)

        point_layout.addWidget(self.edit_selected_button)

        point_layout.addWidget(self.undo_button)

        point_layout.addWidget(self.clear_points_button)

        point_layout.addStretch()

        point_layout.addWidget(self.export_excel_button)

        main_layout.addWidget(point_group)

        # ====================================================
        # TABLE
        # ====================================================

        table_group = QGroupBox("5. Extracted Curve Points")

        table_layout = QVBoxLayout(table_group)

        self.point_table = QTableWidget()

        self.point_table.setColumnCount(4)

        self.point_table.setHorizontalHeaderLabels(
            ["No.", "RPM", "Head (m)", "Flow (m³/h)"]
        )

        self.point_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.point_table.setAlternatingRowColors(True)

        table_layout.addWidget(self.point_table)

        main_layout.addWidget(table_group)

        # ====================================================
        # STATUS
        # ====================================================

        self.status_label = QLabel("Ready")

        self.status_label.setStyleSheet("color: #555555;")

        main_layout.addWidget(self.status_label)

        # ====================================================
        # SIGNALS
        # ====================================================

        self.open_image_button.clicked.connect(self.open_image)

        self.save_project_button.clicked.connect(self.save_project)

        self.open_project_button.clicked.connect(self.open_project)

        self.paste_image_button.clicked.connect(self.paste_image)

        self.clear_image_button.clicked.connect(self.clear_image)

        self.curve_type_input.currentIndexChanged.connect(self.curve_type_changed)

        self.rpm_input.valueChanged.connect(self.rpm_changed)

        self.x_min_button.clicked.connect(lambda: self.start_calibration("x_min"))

        self.x_max_button.clicked.connect(lambda: self.start_calibration("x_max"))

        self.y_min_button.clicked.connect(lambda: self.start_calibration("y_min"))

        self.y_max_button.clicked.connect(lambda: self.start_calibration("y_max"))

        self.clear_calibration_button.clicked.connect(self.clear_calibration)

        self.graph.mouse_clicked.connect(self.graph_clicked)

        self.graph.point_selected.connect(self.select_point)

        self.zoom_in_button.clicked.connect(self.zoom_in)

        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.reset_zoom_button.clicked.connect(self.reset_zoom)

        self.hand_button.toggled.connect(self.set_hand_mode)

        self.select_points_button.clicked.connect(self.start_curve_selection)

        self.delete_last_button.clicked.connect(self.delete_last_point)

        self.delete_selected_button.clicked.connect(self.delete_selected_point)

        self.edit_selected_button.clicked.connect(self.edit_selected_point)

        self.undo_button.clicked.connect(self.undo_last_point)

        self.clear_points_button.clicked.connect(self.clear_current_curve_points)

        self.export_excel_button.clicked.connect(self.export_excel)

        self.point_table.itemSelectionChanged.connect(self.table_point_selected)

        self.curve_selector.currentIndexChanged.connect(
            self.curve_manager_selection_changed
        )

        self.add_curve_button.clicked.connect(self.add_curve)

        self.rename_curve_button.clicked.connect(self.rename_curve)

        self.duplicate_curve_button.clicked.connect(self.duplicate_curve)

        self.delete_curve_button.clicked.connect(self.delete_curve)

        # ----------------------------------------------------
        # INITIAL CURVE MANAGER
        # ----------------------------------------------------

        self.refresh_curve_selector()

        self.curve_selector.blockSignals(True)

        self.curve_selector.setCurrentIndex(0)

        self.curve_selector.blockSignals(False)

        self.active_curve_index = 0

        self.curve_type_input.blockSignals(True)

        self.curve_type_input.setCurrentText(self.curves[0]["type"])

        self.curve_type_input.blockSignals(False)

        self.rpm_input.blockSignals(True)

        self.rpm_input.setValue(self.curves[0]["rpm"])

        self.rpm_input.blockSignals(False)

        self.update_table()

    # ========================================================
    # CURVE MANAGER
    # ========================================================

    def get_current_curve(self):

        if self.active_curve_index < 0 or self.active_curve_index >= len(self.curves):
            return None

        return self.curves[self.active_curve_index]

    def get_current_curve_points(self):

        curve = self.get_current_curve()

        if curve is None:
            return []

        return curve["points"]

    def refresh_graph_points(self):

        points = self.get_current_curve_points()

        self.graph.points = points

        self.graph.update()

    def update_table_headers(self):

        curve = self.get_current_curve()

        if curve is None:
            return

        if curve["type"] == "Head vs Flow":

            self.point_table.setHorizontalHeaderLabels(
                ["No.", "RPM", "Head (m)", "Flow (m³/h)"]
            )

        else:

            self.point_table.setHorizontalHeaderLabels(
                ["No.", "RPM", "Efficiency (%)", "Flow (m³/h)"]
            )

    def refresh_curve_selector(self):

        if not hasattr(self, "curve_selector"):
            return

        self.curve_selector.blockSignals(True)

        self.curve_selector.clear()

        for curve in self.curves:

            self.curve_selector.addItem(curve["name"])

        self.curve_selector.blockSignals(False)

    def curve_manager_selection_changed(self, index):

        if index < 0:
            return

        if index >= len(self.curves):
            return

        self.active_curve_index = index

        curve = self.curves[index]

        self.curve_type_input.blockSignals(True)

        self.curve_type_input.setCurrentText(curve["type"])

        self.curve_type_input.blockSignals(False)

        self.rpm_input.blockSignals(True)

        self.rpm_input.setValue(int(curve["rpm"]))

        self.rpm_input.blockSignals(False)

        self.clear_selected_point()

        self.refresh_graph_points()

        self.update_table()

        self.status_label.setText(f"Active curve: {curve['name']}")

    def add_curve(self):

        new_curve_number = len(self.curves) + 1

        new_curve = {
            "name": f"New Curve {new_curve_number}",
            "type": "Head vs Flow",
            "rpm": 1480,
            "points": [],
        }

        self.curves.append(new_curve)

        self.refresh_curve_selector()

        new_index = len(self.curves) - 1

        self.curve_selector.setCurrentIndex(new_index)

        self.status_label.setText(f"Added curve: {new_curve['name']}")

    def rename_curve(self):

        index = self.active_curve_index

        if index < 0 or index >= len(self.curves):
            return

        current_name = self.curves[index]["name"]

        new_name, ok = QInputDialog.getText(
            self, "Rename Curve", "Enter new curve name:", text=current_name
        )

        if not ok:
            return

        new_name = new_name.strip()

        if not new_name:
            QMessageBox.warning(
                self,
                "Rename Curve",
                "Curve name cannot be blank.",
            )
            return

        for i, curve in enumerate(self.curves):

            if i != index and curve["name"].strip().lower() == new_name.lower():

                QMessageBox.warning(
                    self,
                    "Rename Curve",
                    f"A curve named '{new_name}' already exists.",
                )

                return

        self.curves[index]["name"] = new_name

        self.refresh_curve_selector()

        self.curve_selector.setCurrentIndex(index)

        self.status_label.setText(f"Curve renamed to: {new_name}")

    def duplicate_curve(self):

        index = self.active_curve_index

        if index < 0 or index >= len(self.curves):
            return

        source_curve = self.curves[index]

        base_name = source_curve["name"].strip()

        # ----------------------------------------------------
        # Determine original/base curve name
        # ----------------------------------------------------

        import re

        match = re.match(r"^(.*) - Copy(?: (\d+))?$", base_name)

        if match:
            original_name = match.group(1).strip()
        else:
            original_name = base_name

        # ----------------------------------------------------
        # Find next available Copy number
        # ----------------------------------------------------

        copy_number = 1

        while True:

            if copy_number == 1:
                candidate_name = f"{original_name} - Copy"
            else:
                candidate_name = f"{original_name} - Copy {copy_number}"

            name_exists = any(
                curve["name"].strip().lower() == candidate_name.lower()
                for curve in self.curves
            )

            if not name_exists:
                break

            copy_number += 1

        # ----------------------------------------------------
        # Create duplicated curve
        # ----------------------------------------------------

        duplicated_curve = {
            "name": candidate_name,
            "type": source_curve["type"],
            "rpm": source_curve["rpm"],
            "points": copy.deepcopy(source_curve["points"]),
        }

        self.curves.insert(index + 1, duplicated_curve)

        self.refresh_curve_selector()

        new_index = index + 1

        self.curve_selector.setCurrentIndex(new_index)

        self.status_label.setText(
            f"Duplicated curve: {duplicated_curve['name']}"
        )

    def delete_curve(self):

        index = self.active_curve_index

        if index < 0 or index >= len(self.curves):
            return

        # ----------------------------------------------------
        # PROTECT LAST REMAINING CURVE
        # ----------------------------------------------------

        if len(self.curves) <= 1:

            QMessageBox.warning(
                self,
                "Delete Curve",
                "At least one curve must remain.",
            )

            return

        curve_name = self.curves[index]["name"]

        # ----------------------------------------------------
        # CONFIRM DELETE
        # ----------------------------------------------------

        reply = QMessageBox.question(
            self,
            "Delete Curve",
            "Are you sure you want to delete:\n\n"
            f"{curve_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # ----------------------------------------------------
        # DELETE CURVE
        # ----------------------------------------------------

        del self.curves[index]

        # ----------------------------------------------------
        # DETERMINE NEW ACTIVE CURVE
        # ----------------------------------------------------

        if index >= len(self.curves):
            index = len(self.curves) - 1

        self.active_curve_index = index

        # ----------------------------------------------------
        # CLEAR OLD POINT SELECTION
        # ----------------------------------------------------

        self.clear_selected_point()

        # ----------------------------------------------------
        # REFRESH CURVE SELECTOR
        # ----------------------------------------------------

        self.refresh_curve_selector()

        self.curve_selector.setCurrentIndex(index)

        # ----------------------------------------------------
        # REFRESH ACTIVE CURVE DATA
        # ----------------------------------------------------

        curve = self.get_current_curve()

        if curve is not None:

            self.curve_type_input.blockSignals(True)

            self.curve_type_input.setCurrentText(
                curve["type"]
            )

            self.curve_type_input.blockSignals(False)

            self.rpm_input.blockSignals(True)

            self.rpm_input.setValue(
                int(curve["rpm"])
            )

            self.rpm_input.blockSignals(False)

        # ----------------------------------------------------
        # REFRESH GRAPH AND TABLE
        # ----------------------------------------------------

        self.refresh_graph_points()

        self.update_table_headers()

        self.update_table()

        self.status_label.setText(
            f"Deleted curve: {curve_name}"
        )

    def curve_type_changed(self):

        curve = self.get_current_curve()

        if curve is None:
            return

        new_type = self.curve_type_input.currentText()
        current_type = curve["type"]

        # ----------------------------------------------------
        # NO CHANGE
        # ----------------------------------------------------

        if new_type == current_type:
            return

        # ----------------------------------------------------
        # PROTECT EXISTING DATA
        # ----------------------------------------------------

        if curve["points"]:

            QMessageBox.warning(
                self,
                "Curve Type Change",
                "This curve already contains data points.\n\n"
                "Curve type cannot be changed while points exist.\n\n"
                "Create a new curve for the other curve type.",
            )

            # Restore original curve type in the UI
            self.curve_type_input.blockSignals(True)

            self.curve_type_input.setCurrentText(
                current_type
            )

            self.curve_type_input.blockSignals(False)

            return

        # ----------------------------------------------------
        # CHANGE TYPE — ONLY FOR EMPTY CURVE
        # ----------------------------------------------------

        curve["type"] = new_type

        self.clear_selected_point()

        self.update_table_headers()

        self.refresh_graph_points()

        self.update_table()

        self.status_label.setText(
            f"Active curve type: {curve['type']}"
        )
    def rpm_changed(self, value):

        curve = self.get_current_curve()

        if curve is None:
            return

        new_rpm = int(value)

        # ----------------------------------------------------
        # UPDATE CURVE RPM
        # ----------------------------------------------------

        curve["rpm"] = new_rpm

        # ----------------------------------------------------
        # KEEP ALL EXISTING POINTS CONSISTENT
        # ----------------------------------------------------

        for point in curve["points"]:

            point["rpm"] = new_rpm

        # ----------------------------------------------------
        # REFRESH TABLE
        # ----------------------------------------------------

        self.update_table()

        self.status_label.setText(
            f"RPM updated: {new_rpm}"
        )

    # ========================================================
    # ZOOM
    # ========================================================

    def update_zoom_status(self):

        percentage = int(self.graph.zoom_factor * 100)

        self.zoom_status.setText(f"Zoom: {percentage}%")

    def zoom_in(self):

        self.graph.zoom_in()

        self.update_zoom_status()

    def zoom_out(self):

        self.graph.zoom_out()

        self.update_zoom_status()

    def reset_zoom(self):

        self.graph.reset_zoom()

        self.update_zoom_status()

    def set_hand_mode(self, enabled):

        self.graph.hand_mode = enabled

        if enabled:

            self.graph.setCursor(Qt.OpenHandCursor)

            self.status_label.setText("Hand / Pan mode enabled")

        else:

            self.graph.setCursor(Qt.ArrowCursor)

            self.status_label.setText("Hand / Pan mode disabled")

    # ========================================================
    # PUMP INFORMATION
    # ========================================================

    def get_pump_information(self):

        return {
            "pump_name": self.pump_name_input.text().strip(),
            "manufacturer": self.manufacturer_input.text().strip(),
            "model": self.model_input.text().strip(),
            "pump_type": self.pump_type_input.text().strip(),
            "fluid": self.fluid_input.text().strip(),
            "rpm": self.rpm_input.value(),
            "remarks": self.remarks_input.text().strip(),
        }

    def load_pump_information(self, pump_info):

        if not isinstance(pump_info, dict):
            pump_info = {}

        self.pump_name_input.setText(str(pump_info.get("pump_name", "")))

        self.manufacturer_input.setText(str(pump_info.get("manufacturer", "")))

        self.model_input.setText(str(pump_info.get("model", "")))

        self.pump_type_input.setText(str(pump_info.get("pump_type", "")))

        self.fluid_input.setText(str(pump_info.get("fluid", "")))

        self.remarks_input.setText(str(pump_info.get("remarks", "")))

    def clear_pump_information(self):

        self.pump_name_input.clear()

        self.manufacturer_input.clear()

        self.model_input.clear()

        self.pump_type_input.clear()

        self.fluid_input.clear()

        self.remarks_input.clear()

    # ========================================================
    # OPEN IMAGE
    # ========================================================

    def clear_all_curve_points(self):

        for curve in self.curves:

            curve["points"].clear()

    def open_image(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Graph Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )

        if not file_path:
            return

        pixmap = QPixmap(file_path)

        if pixmap.isNull():

            QMessageBox.warning(self, "Error", "Unable to open the selected image.")

            return

        self.graph_image = pixmap

        self.graph.set_image(pixmap)

        self.clear_calibration_data_only()

        self.clear_all_curve_points()

        self.undo_history = {}

        self.clear_selected_point()

        self.update_table()

        self.clear_pump_information()

        self.current_project_path = None

        self.status_label.setText(
            "Graph image loaded: " f"{os.path.basename(file_path)}"
        )

    # ========================================================
    # PASTE IMAGE
    # ========================================================

    def paste_image(self):

        clipboard = QApplication.clipboard()

        image = clipboard.image()

        if image.isNull():

            QMessageBox.warning(
                self, "Clipboard Empty", "No image was found in the clipboard."
            )

            return

        pixmap = QPixmap.fromImage(image)

        self.graph_image = pixmap

        self.graph.set_image(pixmap)

        self.clear_calibration_data_only()

        self.clear_all_curve_points()

        self.undo_history = {}

        self.clear_selected_point()

        self.update_table()

        self.clear_pump_information()

        self.current_project_path = None

        self.status_label.setText("Screenshot pasted successfully.")

    # ========================================================
    # CLEAR IMAGE
    # ========================================================

    def clear_image(self):

        reply = QMessageBox.question(
            self,
            "Clear Image",
            "Clear the current image, calibration " "and curve points?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        self.graph_image = QPixmap()

        self.graph.set_image(QPixmap())

        self.clear_calibration_data_only()

        self.clear_all_curve_points()

        self.undo_history = {}

        self.clear_selected_point()

        self.update_table()

        self.clear_pump_information()

        self.current_project_path = None

        self.status_label.setText("Image cleared.")

    # ========================================================
    # SAVE PROJECT
    # ========================================================

    def save_project(self):

        if self.graph_image.isNull():

            QMessageBox.warning(
                self, "No Image", "Please open or paste a graph image first."
            )

            return

        if not self.is_calibrated():

            reply = QMessageBox.question(
                self,
                "Calibration Not Completed",
                "Calibration is not completed.\n\n"
                "Do you still want to save the project?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Pump Curve Project",
            "Pump_Curve_Project.json",
            "Project Files (*.json)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".json"):

            file_path += ".json"

        project_dir = os.path.dirname(file_path)

        project_name = os.path.splitext(os.path.basename(file_path))[0]

        image_filename = project_name + "_graph.png"

        image_path = os.path.join(project_dir, image_filename)

        if not self.graph_image.save(image_path, "PNG"):

            QMessageBox.warning(
                self, "Image Save Error", "Unable to save the graph image."
            )

            return

        calibration_data = {
            "x_min_pixel": self.x_min_pixel,
            "x_max_pixel": self.x_max_pixel,
            "y_min_pixel": self.y_min_pixel,
            "y_max_pixel": self.y_max_pixel,
            "x_min_value": self.x_min_input.text(),
            "x_max_value": self.x_max_input.text(),
            "y_min_value": self.y_min_input.text(),
            "y_max_value": self.y_max_input.text(),
        }

        project_data = {
            "project_version": "1.5.1",
            "active_curve_index": self.active_curve_index,
            "active_curve": (
                self.get_current_curve()["type"]
                if self.get_current_curve()
                else "Head vs Flow"
            ),
            "curves": copy.deepcopy(self.curves),
            # Backward compatibility
            "head_curve_points": copy.deepcopy(self.head_curve_points),
            "efficiency_curve_points": copy.deepcopy(self.efficiency_curve_points),
            "rpm": self.rpm_input.value(),
            "pump_information": self.get_pump_information(),
            "calibration": calibration_data,
            "graph_image": image_filename,
        }

        try:

            with open(file_path, "w", encoding="utf-8") as file:

                json.dump(project_data, file, indent=4)

            self.current_project_path = file_path

            QMessageBox.information(
                self,
                "Project Saved",
                "Project saved successfully.\n\n"
                f"Project: "
                f"{os.path.basename(file_path)}\n"
                f"Graph: {image_filename}",
            )

            self.status_label.setText("Project saved successfully.")

        except Exception as error:

            QMessageBox.critical(
                self, "Save Error", "Unable to save project.\n\n" f"{error}"
            )

    # ========================================================
    # OPEN PROJECT
    # ========================================================

    def open_project(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Pump Curve Project", "", "Project Files (*.json)"
        )

        if not file_path:
            return

        try:

            with open(file_path, "r", encoding="utf-8") as file:

                project_data = json.load(file)

            project_version = project_data.get("project_version", "1.3.1 / Older")

            # ------------------------------------------------
            # GRAPH IMAGE
            # ------------------------------------------------

            image_filename = project_data.get("graph_image", "")

            image_filename = os.path.basename(image_filename)

            project_dir = os.path.dirname(file_path)

            image_path = os.path.join(project_dir, image_filename)

            if not os.path.exists(image_path):

                QMessageBox.warning(
                    self,
                    "Graph Image Missing",
                    "The project file was found, but "
                    "its graph image could not be found.\n\n"
                    f"Expected:\n{image_path}",
                )

                return

            pixmap = QPixmap(image_path)

            if pixmap.isNull():

                QMessageBox.warning(
                    self, "Image Error", "The graph image could not be loaded."
                )

                return

            self.graph_image = pixmap

            self.graph.set_image(pixmap)

            # ------------------------------------------------
            # PUMP INFORMATION
            # ------------------------------------------------

            pump_info = project_data.get("pump_information", {})

            self.load_pump_information(pump_info)

            # ------------------------------------------------
            # CALIBRATION
            # ------------------------------------------------

            calibration = project_data.get("calibration", {})

            if not isinstance(calibration, dict):
                calibration = {}

            self.x_min_pixel = calibration.get("x_min_pixel", None)

            self.x_max_pixel = calibration.get("x_max_pixel", None)

            self.y_min_pixel = calibration.get("y_min_pixel", None)

            self.y_max_pixel = calibration.get("y_max_pixel", None)

            self.x_min_input.setText(str(calibration.get("x_min_value", "")))

            self.x_max_input.setText(str(calibration.get("x_max_value", "")))

            self.y_min_input.setText(str(calibration.get("y_min_value", "")))

            self.y_max_input.setText(str(calibration.get("y_max_value", "")))

            # ------------------------------------------------
            # CURVE DATA
            # ------------------------------------------------

            saved_curves = project_data.get("curves", None)

            if isinstance(saved_curves, list) and len(saved_curves) > 0:

                self.curves = []

                for saved_curve in saved_curves:

                    if not isinstance(saved_curve, dict):
                        continue

                    curve_name = str(saved_curve.get("name", "Curve"))

                    curve_type = str(saved_curve.get("type", "Head vs Flow"))

                    if curve_type not in ["Head vs Flow", "Efficiency vs Flow"]:

                        curve_type = "Head vs Flow"

                    try:

                        curve_rpm = int(saved_curve.get("rpm", 1480))

                    except:

                        curve_rpm = 1480

                    curve_rpm = max(1, min(100000, curve_rpm))

                    saved_points = saved_curve.get("points", [])

                    if not isinstance(saved_points, list):

                        saved_points = []

                    self.curves.append(
                        {
                            "name": curve_name,
                            "type": curve_type,
                            "rpm": curve_rpm,
                            "points": copy.deepcopy(saved_points),
                        }
                    )

            else:

                # ------------------------------------------------
                # OLD PROJECT COMPATIBILITY
                # ------------------------------------------------

                head_points = project_data.get("head_curve_points", [])

                efficiency_points = project_data.get("efficiency_curve_points", [])

                if not isinstance(head_points, list):

                    head_points = []

                if not isinstance(efficiency_points, list):

                    efficiency_points = []

                self.curves = [
                    {
                        "name": "Head vs Flow - 1480 RPM",
                        "type": "Head vs Flow",
                        "rpm": 1480,
                        "points": copy.deepcopy(head_points),
                    },
                    {
                        "name": "Efficiency vs Flow - 1480 RPM",
                        "type": "Efficiency vs Flow",
                        "rpm": 1480,
                        "points": copy.deepcopy(efficiency_points),
                    },
                ]

            # ------------------------------------------------
            # REBUILD LEGACY REFERENCES
            # ------------------------------------------------

            self.head_curve_points = []

            self.efficiency_curve_points = []

            for curve in self.curves:

                if curve["type"] == "Head vs Flow":

                    if not self.head_curve_points:

                        self.head_curve_points = curve["points"]

                elif curve["type"] == "Efficiency vs Flow":

                    if not self.efficiency_curve_points:

                        self.efficiency_curve_points = curve["points"]

            # ------------------------------------------------
            # ACTIVE CURVE
            # ------------------------------------------------

            try:

                active_index = int(project_data.get("active_curve_index", 0))

            except:

                active_index = 0

            if active_index < 0 or active_index >= len(self.curves):

                active_index = 0

            self.active_curve_index = active_index

            self.refresh_curve_selector()

            self.curve_selector.blockSignals(True)

            self.curve_selector.setCurrentIndex(active_index)

            self.curve_selector.blockSignals(False)

            active_curve = self.curves[active_index]

            self.curve_type_input.blockSignals(True)

            self.curve_type_input.setCurrentText(active_curve["type"])

            self.curve_type_input.blockSignals(False)

            self.rpm_input.blockSignals(True)

            self.rpm_input.setValue(active_curve["rpm"])

            self.rpm_input.blockSignals(False)

            # ------------------------------------------------
            # UNDO / REFRESH
            # ------------------------------------------------

            self.undo_history = {}

            self.clear_selected_point()

            self.refresh_graph_points()

            self.update_table_headers()

            self.update_table()

            self.select_points_button.setChecked(False)

            self.graph.set_point_selection_mode(False)

            self.calibration_mode = None

            self.current_project_path = file_path

            self.check_calibration()

            self.status_label.setText(
                "Project loaded successfully. " f"Version: {project_version}"
            )

            QMessageBox.information(
                self,
                "Project Loaded",
                "Project loaded successfully.\n\n"
                f"Project version: {project_version}",
            )

        except json.JSONDecodeError:

            QMessageBox.warning(
                self, "Invalid Project", "The project file is not valid JSON."
            )

    # ========================================================
    # CALIBRATION
    # ========================================================

    def start_calibration(self, mode):

        if self.graph_image.isNull():

            QMessageBox.warning(
                self, "No Image", "Please open or paste a graph image first."
            )

            return

        self.calibration_mode = mode

        names = {"x_min": "X Min", "x_max": "X Max", "y_min": "Y Min", "y_max": "Y Max"}

        self.calibration_status.setText(f"Select pixel position for " f"{names[mode]}")

        self.calibration_status.setStyleSheet("color: #b06000;")

        self.status_label.setText(f"Click graph to select " f"{names[mode]} pixel.")

    def graph_clicked(self, pixel_x, pixel_y):

        # ----------------------------------------------------
        # CALIBRATION MODE
        # ----------------------------------------------------

        if self.calibration_mode:

            mode = self.calibration_mode

            if mode == "x_min":

                self.x_min_pixel = pixel_x

            elif mode == "x_max":

                self.x_max_pixel = pixel_x

            elif mode == "y_min":

                self.y_min_pixel = pixel_y

            elif mode == "y_max":

                self.y_max_pixel = pixel_y

            self.calibration_mode = None

            self.check_calibration()

            return

        # ----------------------------------------------------
        # CURVE POINT MODE
        # ----------------------------------------------------

        if self.select_points_button.isChecked():

            self.add_curve_point(pixel_x, pixel_y)

    # ========================================================
    # CHECK CALIBRATION
    # ========================================================

    def check_calibration(self):
        complete = (
            self.x_min_pixel is not None
            and self.x_max_pixel is not None
            and self.y_min_pixel is not None
            and self.y_max_pixel is not None
        )

        if not complete:

            missing = []

            if self.x_min_pixel is None:
                missing.append("X Min")

            if self.x_max_pixel is None:
                missing.append("X Max")

            if self.y_min_pixel is None:
                missing.append("Y Min")

            if self.y_max_pixel is None:
                missing.append("Y Max")

            self.calibration_status.setText(
                "Calibration incomplete: "
                + ", ".join(missing)
                + " pixel required"
            )

            self.calibration_status.setStyleSheet(
                "color: #b00020;"
            )

            return False
        if self.x_max_pixel == self.x_min_pixel:
            self.calibration_status.setText(
                "Invalid X calibration"
            )
            self.calibration_status.setStyleSheet(
                "color: #b00020;"
            )
            return False

        if self.y_max_pixel == self.y_min_pixel:
            self.calibration_status.setText(
                "Invalid Y calibration"
            )
            self.calibration_status.setStyleSheet(
                "color: #b00020;"
            )
            return False

        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
            y_min = float(self.y_min_input.text())
            y_max = float(self.y_max_input.text())
        except (ValueError, TypeError):
            self.calibration_status.setText(
                "Invalid calibration values"
            )
            self.calibration_status.setStyleSheet(
                "color: #b00020;"
            )
            return False

        if x_max == x_min:
            self.calibration_status.setText(
                "Invalid X calibration range"
            )
            self.calibration_status.setStyleSheet(
                "color: #b00020;"
            )
            return False

        if y_max == y_min:
            self.calibration_status.setText(
                "Invalid Y calibration range"
            )
            self.calibration_status.setStyleSheet(
                "color: #b00020;"
            )
            return False

        self.calibration_status.setText(
            "Calibration completed successfully"
        )
        self.calibration_status.setStyleSheet(
            "color: #008000;"
        )
        return True

    def is_calibrated(self):
        return self.check_calibration()


    # ========================================================
    # CLEAR CALIBRATION
    # ========================================================

    def clear_calibration_data_only(self):

        self.x_min_pixel = None

        self.x_max_pixel = None

        self.y_min_pixel = None

        self.y_max_pixel = None

        self.calibration_mode = None

        self.x_min_input.clear()

        self.x_max_input.clear()

        self.y_min_input.clear()

        self.y_max_input.clear()

        self.calibration_status.setText("Calibration not completed")

        self.calibration_status.setStyleSheet("color: #b00020;")

    def clear_calibration(self):

        self.clear_calibration_data_only()

        self.status_label.setText("Calibration cleared.")

    # ========================================================
    # START CURVE SELECTION
    # ========================================================

    def start_curve_selection(self):
        if not self.select_points_button.isChecked():
            self.graph.set_point_selection_mode(False)

            self.status_label.setText("Curve point selection stopped.")

            return

        if not self.is_calibrated():
            self.select_points_button.setChecked(False)

            self.graph.set_point_selection_mode(False)

            QMessageBox.warning(
                self,
                "Calibration Required",
                "Please complete X and Y calibration " "before selecting curve points.",
            )

            return

        self.graph.set_point_selection_mode(True)

        current_points = self.get_current_curve_points()

        curve = self.get_current_curve()

        if curve is None:
            return

        self.status_label.setText(
            f"Select points for "
            f"{curve['name']}. "
            f"Existing points: "
            f"{len(current_points)}"
        )

    # ========================================================
    # POINT SELECTION
    # ========================================================

    def select_point(self, index):

        points = self.get_current_curve_points()

        if index < 0 or index >= len(points):

            self.selected_point_index = None

            self.graph.selected_point_index = None

            self.point_table.clearSelection()

            self.graph.update()

            return

        self.selected_point_index = index

        self.graph.selected_point_index = index

        self.point_table.blockSignals(True)

        self.point_table.selectRow(index)

        self.point_table.blockSignals(False)

        self.status_label.setText(f"Selected Point {index + 1}.")

        self.graph.update()

    def table_point_selected(self):

        row = self.point_table.currentRow()

        if row >= 0:

            self.select_point(row)

    def clear_selected_point(self):

        self.selected_point_index = None

        self.graph.selected_point_index = None

        self.point_table.clearSelection()

        self.graph.update()

    # ========================================================
    # UNDO
    # ========================================================

    def push_undo_snapshot(self):

        curve = self.get_current_curve()

        if curve is None:
            return

        curve_id = id(curve)

        if curve_id not in self.undo_history:

            self.undo_history[curve_id] = []

        history = self.undo_history[curve_id]

        history.append(copy.deepcopy(curve["points"]))

        if len(history) > 50:

            history.pop(0)

    def restore_undo_snapshot(self):

        curve = self.get_current_curve()

        if curve is None:
            return

        curve_id = id(curve)

        history = self.undo_history.get(curve_id, [])

        if not history:

            self.status_label.setText("No undo history available.")

            return

        previous_points = history.pop()

        curve["points"].clear()

        curve["points"].extend(copy.deepcopy(previous_points))

        self.clear_selected_point()

        self.refresh_graph_points()

        self.update_table()

        self.status_label.setText("Last point action undone.")

    # ========================================================
    # EDIT POINT
    # ========================================================

    def edit_selected_point(self):

        points = self.get_current_curve_points()

        curve = self.get_current_curve()

        if curve is None:
            return

        if self.selected_point_index is None:

            QMessageBox.information(
                self,
                "No Point Selected",
                "Please select a point from " "the graph or table first.",
            )

            return

        if self.selected_point_index < 0 or self.selected_point_index >= len(points):

            self.clear_selected_point()

            return

        point = points[self.selected_point_index]

        dialog = QDialog(self)

        dialog.setWindowTitle("Edit Curve Point")

        dialog.setModal(True)

        layout = QGridLayout(dialog)

        layout.addWidget(QLabel("Flow (m³/h):"), 0, 0)

        flow_input = QDoubleSpinBox()

        flow_input.setRange(-1000000000, 1000000000)

        flow_input.setDecimals(6)

        flow_input.setValue(float(point.get("flow", 0)))

        layout.addWidget(flow_input, 0, 1)

        if curve["type"] == "Head vs Flow":

            value_label = "Head (m):"

            value_key = "head"

        else:

            value_label = "Efficiency (%):"

            value_key = "efficiency"

        layout.addWidget(QLabel(value_label), 1, 0)

        value_input = QDoubleSpinBox()

        value_input.setRange(-1000000000, 1000000000)

        value_input.setDecimals(6)

        value_input.setValue(float(point.get(value_key, 0)))

        layout.addWidget(value_input, 1, 1)

        layout.addWidget(QLabel("RPM:"), 2, 0)

        rpm_input = QSpinBox()

        rpm_input.setRange(1, 100000)

        rpm_input.setValue(int(point.get("rpm", curve["rpm"])))

        layout.addWidget(rpm_input, 2, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons.accepted.connect(dialog.accept)

        buttons.rejected.connect(dialog.reject)

        layout.addWidget(buttons, 3, 0, 1, 2)

        if dialog.exec() != QDialog.Accepted:
            return

        self.push_undo_snapshot()

        point["flow"] = flow_input.value()

        point[value_key] = value_input.value()

        point["rpm"] = rpm_input.value()

        # ----------------------------------------------------
        # RECALCULATE PIXEL POSITION
        # ----------------------------------------------------

        try:

            x_min = float(self.x_min_input.text())

            x_max = float(self.x_max_input.text())

            y_min = float(self.y_min_input.text())

            y_max = float(self.y_max_input.text())

            if x_max == x_min or y_max == y_min:

                raise ValueError

            x_fraction = (point["flow"] - x_min) / (x_max - x_min)

            y_fraction = (point[value_key] - y_min) / (y_max - y_min)

            point["pixel_x"] = self.x_min_pixel + x_fraction * (
                self.x_max_pixel - self.x_min_pixel
            )

            point["pixel_y"] = self.y_min_pixel + y_fraction * (
                self.y_max_pixel - self.y_min_pixel
            )

        except (ValueError, TypeError, ZeroDivisionError):

            QMessageBox.warning(
                self,
                "Calibration Required",
                "The point values were updated, "
                "but the graph position could not "
                "be recalculated because calibration "
                "values are invalid or incomplete.",
            )

        self.refresh_graph_points()

        self.update_table()

        self.select_point(self.selected_point_index)

        self.status_label.setText(
            f"Point " f"{self.selected_point_index + 1} " f"updated successfully."
        )

    # ========================================================
    # ADD CURVE POINT
    # ========================================================

    def add_curve_point(self, pixel_x, pixel_y):

        if not self.is_calibrated():
            return

        curve = self.get_current_curve()

        if curve is None:
            return

        try:

            x_min = float(self.x_min_input.text())

            x_max = float(self.x_max_input.text())

            y_min = float(self.y_min_input.text())

            y_max = float(self.y_max_input.text())

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Calibration Values",
                "Please enter valid numerical values "
                "for X Min, X Max, Y Min and Y Max.",
            )

            self.select_points_button.setChecked(False)

            return

        if self.x_max_pixel == self.x_min_pixel:

            QMessageBox.warning(
                self, "Invalid Calibration", "X calibration range is invalid."
            )

            return

        if self.y_max_pixel == self.y_min_pixel:

            QMessageBox.warning(
                self, "Invalid Calibration", "Y calibration range is invalid."
            )

            return

        # ----------------------------------------------------
        # X CONVERSION
        # ----------------------------------------------------

        x_fraction = (pixel_x - self.x_min_pixel) / (
            self.x_max_pixel - self.x_min_pixel
        )

        x_value = x_min + x_fraction * (x_max - x_min)

        # ----------------------------------------------------
        # Y CONVERSION
        # ----------------------------------------------------

        y_fraction = (pixel_y - self.y_min_pixel) / (
            self.y_max_pixel - self.y_min_pixel
        )

        y_value = y_min + y_fraction * (y_max - y_min)

        # ----------------------------------------------------
        # ENGINEERING RANGE VALIDATION
        # ----------------------------------------------------

        x_range_min = min(x_min, x_max)
        x_range_max = max(x_min, x_max)

        y_range_min = min(y_min, y_max)
        y_range_max = max(y_min, y_max)

        if not (x_range_min <= x_value <= x_range_max):

            QMessageBox.warning(
                self,
                "Point Outside Calibration",
                "The selected point is outside the calibrated "
                "Flow range.\n\n"
                f"Flow = {x_value:.3f}\n"
                f"Valid range = {x_range_min:.3f} to {x_range_max:.3f}",
            )

            return

        if not (y_range_min <= y_value <= y_range_max):

            QMessageBox.warning(
                self,
                "Point Outside Calibration",
                "The selected point is outside the calibrated "
                "value range.\n\n"
                f"Value = {y_value:.3f}\n"
                f"Valid range = {y_range_min:.3f} to {y_range_max:.3f}",
            )

            return

        # ----------------------------------------------------
        # DUPLICATE POINT CHECK
        # ----------------------------------------------------

        value_key = (
            "head"
            if curve["type"] == "Head vs Flow"
            else "efficiency"
        )

        duplicate_point = None

        for existing_point in curve["points"]:

            existing_flow = existing_point.get("flow")

            existing_value = existing_point.get(value_key)

            if existing_flow is None or existing_value is None:
                continue

            if (
                abs(existing_flow - x_value) <= 0.000001
                and abs(existing_value - y_value) <= 0.000001
            ):
                duplicate_point = existing_point
                break

        if duplicate_point is not None:

            reply = QMessageBox.question(
                self,
                "Similar Point Detected",
                "A point with the same Flow and "
                f"{'Head' if value_key == 'head' else 'Efficiency'} "
                "already exists in this curve.\n\n"
                f"Flow = {x_value:.6f}\n"
                f"Value = {y_value:.6f}\n\n"
                "Do you want to add this point anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                self.status_label.setText(
                    "Duplicate point not added."
                )
                return

        # ----------------------------------------------------
        # UNDO
        # ----------------------------------------------------

        self.push_undo_snapshot()

        # ----------------------------------------------------
        # POINT
        # ----------------------------------------------------

        point = {
            "rpm": curve["rpm"],
            "flow": x_value,
            "pixel_x": pixel_x,
            "pixel_y": pixel_y,
        }

        if curve["type"] == "Head vs Flow":

            point["head"] = y_value

        else:

            point["efficiency"] = y_value

        # ----------------------------------------------------
        # IMPORTANT:
        # ADD TO ACTIVE CURVE
        # ----------------------------------------------------

        curve["points"].append(point)

        # ----------------------------------------------------
        # REFRESH
        # ----------------------------------------------------

        self.refresh_graph_points()

        self.update_table()

        current_points = self.get_current_curve_points()

        self.status_label.setText(
            f"Point {len(current_points)} added. " f"Flow = {x_value:.3f}"
        )

    # ========================================================
    # UPDATE TABLE
    # ========================================================

    def update_table(self):

        points = self.get_current_curve_points()

        curve = self.get_current_curve()

        self.point_table.setRowCount(len(points))

        if curve is None:
            return

        self.update_table_headers()

        for row, point in enumerate(points):

            self.point_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            self.point_table.setItem(
                row, 1, QTableWidgetItem(str(point.get("rpm", curve["rpm"])))
            )

            if curve["type"] == "Head vs Flow":

                value = point.get("head", "")

            else:

                value = point.get("efficiency", "")

            flow = point.get("flow", "")

            if isinstance(value, (int, float)):

                value_text = f"{value:.3f}"

            else:

                value_text = str(value)

            if isinstance(flow, (int, float)):

                flow_text = f"{flow:.3f}"

            else:

                flow_text = str(flow)

            self.point_table.setItem(row, 2, QTableWidgetItem(value_text))

            self.point_table.setItem(row, 3, QTableWidgetItem(flow_text))

    # ========================================================
    # DELETE LAST POINT
    # ========================================================

    def delete_last_point(self):

        points = self.get_current_curve_points()

        if not points:

            self.status_label.setText("No points available to delete.")

            return

        self.push_undo_snapshot()

        points.pop()

        self.clear_selected_point()

        self.refresh_graph_points()

        self.update_table()

        self.status_label.setText("Last point deleted.")

    # ========================================================
    # DELETE SELECTED POINT
    # ========================================================

    def delete_selected_point(self):

        points = self.get_current_curve_points()

        if self.selected_point_index is None:

            QMessageBox.information(
                self,
                "No Point Selected",
                "Please select a point from " "the graph or table first.",
            )

            return

        if self.selected_point_index < 0 or self.selected_point_index >= len(points):

            self.clear_selected_point()

            return

        point_number = self.selected_point_index + 1

        reply = QMessageBox.question(
            self,
            "Delete Selected Point",
            f"Delete Point {point_number} " "from the current curve?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        self.push_undo_snapshot()

        points.pop(self.selected_point_index)

        self.clear_selected_point()

        self.refresh_graph_points()

        self.update_table()

        self.status_label.setText(
            f"Point {point_number} deleted. " "Remaining points renumbered."
        )

    def undo_last_point(self):

        self.restore_undo_snapshot()

    # ========================================================
    # CLEAR CURRENT CURVE POINTS
    # ========================================================

    def clear_current_curve_points(self):

        points = self.get_current_curve_points()

        if not points:

            self.status_label.setText("No points available.")

            return

        curve = self.get_current_curve()

        if curve is None:
            return

        reply = QMessageBox.question(
            self,
            "Clear Curve Points",
            "Clear all points from the current curve?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        self.push_undo_snapshot()

        curve["points"].clear()

        self.clear_selected_point()

        self.refresh_graph_points()

        self.update_table()

        self.status_label.setText("Current curve points cleared.")

    # ========================================================
    # EXPORT EXCEL
    # ========================================================

    def export_excel(self):

        has_points = False

        for curve in self.curves:

            if curve["points"]:

                has_points = True
                break

        if not has_points:

            QMessageBox.warning(
                self, "No Data", "No curve points are available for export."
            )

            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Curve Data", "Pump_Curve_Data.xlsx", "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".xlsx"):

            file_path += ".xlsx"

        try:

            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:

                # ------------------------------------------------
                # CURVES
                # ------------------------------------------------

                for curve_index, curve in enumerate(self.curves):

                    points = curve["points"]

                    if not points:
                        continue

                    data = []

                    for index, point in enumerate(points):

                        row = {
                            "No.": index + 1,
                            "RPM": point.get("rpm", curve["rpm"]),
                            "Flow (m3/h)": point.get("flow", ""),
                        }

                        if curve["type"] == "Head vs Flow":

                            row["Head (m)"] = point.get("head", "")

                        else:

                            row["Efficiency (%)"] = point.get("efficiency", "")

                        data.append(row)

                    df = pd.DataFrame(data)

                    sheet_name = curve["name"].replace("/", "-").replace("\\", "-")

                    if len(sheet_name) > 31:

                        sheet_name = sheet_name[:31]

                    if not sheet_name:

                        sheet_name = f"Curve {curve_index + 1}"

                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                # ------------------------------------------------
                # PUMP INFORMATION
                # ------------------------------------------------

                pump_info = self.get_pump_information()

                pump_info_data = [
                    {"Parameter": "Pump Name", "Value": pump_info["pump_name"]},
                    {"Parameter": "Manufacturer", "Value": pump_info["manufacturer"]},
                    {"Parameter": "Model", "Value": pump_info["model"]},
                    {"Parameter": "Pump Type", "Value": pump_info["pump_type"]},
                    {"Parameter": "Fluid", "Value": pump_info["fluid"]},
                    {"Parameter": "RPM", "Value": pump_info["rpm"]},
                    {"Parameter": "Remarks", "Value": pump_info["remarks"]},
                ]

                pump_df = pd.DataFrame(pump_info_data)

                pump_df.to_excel(writer, sheet_name="Pump Information", index=False)

            QMessageBox.information(
                self, "Export Successful", "Curve data exported successfully."
            )

            self.status_label.setText("Excel export completed successfully.")

        except Exception as error:

            QMessageBox.critical(
                self, "Export Error", "Unable to export Excel file.\n\n" f"{error}"
            )


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setApplicationName("PumpCurvX")

    app.setWindowIcon(QIcon("PumpCurvX.ico"))

    window = PumpCurveApp()

    window.show()

    sys.exit(app.exec())
