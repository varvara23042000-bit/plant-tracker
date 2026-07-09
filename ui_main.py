import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QSplitter, QDateEdit,
    QSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap, QImage, QColor

from PIL import Image
import database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Трекер комнатных растений")
        self.resize(1100, 700)
        self.setMinimumSize(900, 550)

        self.db = database.DatabaseManager()
        self.current_image_path = ""
        self.current_plant_id = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self._setup_ui()
        self._apply_styles()
        self._bind_signals()

        self._refresh_table()
        self._update_needing_water_status()

    def _setup_ui(self):
        main_layout = QHBoxLayout()
        self.centralWidget().setLayout(main_layout)

        # Левая панель
        left = QWidget()
        left_layout = QVBoxLayout(left)

        left_layout.addWidget(QLabel("Мои растения"))
        left_layout.addWidget(self._create_table())
        left_layout.addLayout(self._create_buttons())
        left_layout.addWidget(self._create_status_label())

        # Правая панель
        right = QWidget()
        right_layout = QVBoxLayout(right)

        right_layout.addWidget(QLabel("Информация о растении"))
        right_layout.addWidget(self._create_form())
        right_layout.addWidget(self._create_image_label())
        right_layout.addLayout(self._create_image_buttons())
        right_layout.addLayout(self._create_action_buttons())
        right_layout.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)

    def _create_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Вид", "Последний полив", "Период", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        return self.table

    def _create_buttons(self):
        layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_water = QPushButton("Отметить полив")
        self.btn_refresh = QPushButton("Обновить")
        for btn in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_water, self.btn_refresh]:
            layout.addWidget(btn)
        return layout

    def _create_status_label(self):
        self.lbl_needing_water = QLabel("Нет растений, требующих полива")
        self.lbl_needing_water.setStyleSheet(
            "background-color: #C8E6C9; padding: 8px; border-radius: 6px; color: #1B5E20;"
        )
        return self.lbl_needing_water

    def _create_form(self):
        form = QWidget()
        layout = QFormLayout(form)

        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("Монстера")
        self.le_species = QLineEdit()
        self.le_species.setPlaceholderText("Monstera deliciosa")
        self.de_watered = QDateEdit()
        self.de_watered.setDate(QDate(2026, 7, 4))
        self.de_watered.setCalendarPopup(True)
        self.spin_frequency = QSpinBox()
        self.spin_frequency.setRange(1, 365)
        self.spin_frequency.setValue(7)
        self.spin_frequency.setSuffix(" дн.")
        self.te_notes = QTextEdit()
        self.te_notes.setMaximumHeight(80)
        self.te_notes.setPlaceholderText("Заметки по уходу...")

        layout.addRow("Название:", self.le_name)
        layout.addRow("Вид:", self.le_species)
        layout.addRow("Последний полив:", self.de_watered)
        layout.addRow("Период полива:", self.spin_frequency)
        layout.addRow("Заметки:", self.te_notes)
        return form

    def _create_image_label(self):
        self.lbl_image = QLabel("Фото растения")
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setMinimumHeight(180)
        self.lbl_image.setStyleSheet("""
            background-color: #E8F5E9;
            border: 2px dashed #66BB6A;
            border-radius: 8px;
            font-size: 14px;
            color: #2E7D32;
        """)
        return self.lbl_image

    def _create_image_buttons(self):
        layout = QHBoxLayout()
        self.btn_load_img = QPushButton("Загрузить фото")
        self.btn_clear_img = QPushButton("Удалить фото")
        layout.addWidget(self.btn_load_img)
        layout.addWidget(self.btn_clear_img)
        return layout

    def _create_action_buttons(self):
        layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_clear = QPushButton("Очистить")
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_clear)
        return layout

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #E8F5E9; }
            QPushButton {
                background-color: #43A047; color: white; border: none;
                padding: 8px 16px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:pressed { background-color: #2E7D32; }
            QPushButton#btn_delete { background-color: #C62828; }
            QPushButton#btn_delete:hover { background-color: #B71C1C; }
            QTableWidget {
                background-color: white; alternate-background-color: #F1F8E9;
                gridline-color: #A5D6A7; border-radius: 8px;
            }
            QTableWidget::item:selected { background-color: #81C784; color: white; }
            QHeaderView::section {
                background-color: #66BB6A; padding: 6px; border: none;
                font-weight: bold; color: white;
            }
            QLineEdit, QTextEdit, QDateEdit, QSpinBox {
                border: 1px solid #A5D6A7; border-radius: 6px;
                padding: 8px; background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QSpinBox:focus {
                border-color: #43A047;
            }
            QLabel { color: #1B5E20; }
            QSplitter::handle { background-color: #81C784; }
        """)

    def _bind_signals(self):
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_water.clicked.connect(self._on_water)
        self.btn_refresh.clicked.connect(self._on_refresh)
        self.btn_load_img.clicked.connect(self._on_load_image)
        self.btn_clear_img.clicked.connect(self._on_clear_image)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_clear.clicked.connect(self._clear_form)
        self.table.itemSelectionChanged.connect(self._on_select_row)

    def _on_add(self):
        self._clear_form()
        self.current_plant_id = None
        self.le_name.setFocus()

    def _on_edit(self):
        row = self._get_selected_row()
        if row is None:
            return
        plant = self.db.get_plant_by_id(self.table.item(row, 0).data(Qt.UserRole))
        if plant:
            self.current_plant_id = plant["id"]
            self.le_name.setText(plant["name"])
            self.le_species.setText(plant["species"] or "")
            self.de_watered.setDate(QDate.fromString(plant["last_watered"], "yyyy-MM-dd"))
            self.spin_frequency.setValue(plant["frequency"])
            self.te_notes.setText(plant["notes"] or "")
            self.current_image_path = plant["image_path"] or ""
            self._load_or_clear_image(self.current_image_path)

    def _on_delete(self):
        row = self._get_selected_row()
        if row is None:
            return
        name = self.table.item(row, 1).text()
        plant_id = self.table.item(row, 0).data(Qt.UserRole)
        if QMessageBox.question(self, "Удаление", f"Удалить '{name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_plant(plant_id)
            self._refresh_table()
            self._clear_form()
            self._update_needing_water_status()

    def _on_water(self):
        row = self._get_selected_row()
        if row is None:
            return
        plant_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 1).text()
        self.db.update_watering_date(plant_id)
        self._refresh_table()
        self._update_needing_water_status()
        QMessageBox.information(self, "Успех", f"Полив для '{name}' отмечен.")

    def _on_refresh(self):
        self._refresh_table()
        self._update_needing_water_status()
        QMessageBox.information(self, "Обновлено", "Данные обновлены.")

    def _on_select_row(self):
        row = self._get_selected_row()
        if row is None:
            return
        plant = self.db.get_plant_by_id(self.table.item(row, 0).data(Qt.UserRole))
        if plant:
            self.current_plant_id = plant["id"]
            self.le_name.setText(plant["name"])
            self.le_species.setText(plant["species"] or "")
            self.de_watered.setDate(QDate.fromString(plant["last_watered"], "yyyy-MM-dd"))
            self.spin_frequency.setValue(plant["frequency"])
            self.te_notes.setText(plant["notes"] or "")
            self.current_image_path = plant["image_path"] or ""
            self._load_or_clear_image(self.current_image_path)

    def _on_load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.current_image_path = path
            self._load_and_display_image(path)

    def _on_clear_image(self):
        self.current_image_path = ""
        self._clear_image_display()

    def _load_and_display_image(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((240, 240), Image.LANCZOS)
            data = img.tobytes("raw", "RGBA")
            qt_img = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            self.lbl_image.setPixmap(QPixmap.fromImage(qt_img))
            self.lbl_image.setScaledContents(True)
            self.lbl_image.setStyleSheet("border: 2px solid #43A047; border-radius: 8px;")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение:\n{e}")
            self._clear_image_display()

    def _load_or_clear_image(self, path):
        if path:
            self._load_and_display_image(path)
        else:
            self._clear_image_display()

    def _clear_image_display(self):
        self.lbl_image.setText("Фото растения")
        self.lbl_image.setPixmap(QPixmap())
        self.lbl_image.setStyleSheet("""
            background-color: #E8F5E9;
            border: 2px dashed #66BB6A;
            border-radius: 8px;
            font-size: 14px;
            color: #2E7D32;
        """)

    def _on_save(self):
        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название обязательно.")
            return

        data = {
            "name": name,
            "species": self.le_species.text().strip(),
            "last_watered": self.de_watered.date().toString("yyyy-MM-dd"),
            "frequency": self.spin_frequency.value(),
            "notes": self.te_notes.toPlainText().strip(),
            "image_path": self.current_image_path
        }

        try:
            if self.current_plant_id:
                data["id"] = self.current_plant_id
                self.db.update_plant(data)
                msg = f"'{name}' обновлено."
            else:
                self.current_plant_id = self.db.insert_plant(data)
                msg = f"'{name}' добавлено."

            self._refresh_table()
            self._clear_form()
            self._update_needing_water_status()
            QMessageBox.information(self, "Успех", msg)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def _refresh_table(self):
        self.table.setRowCount(0)
        plants = self.db.get_all()
        today = datetime.now().date()

        for i, p in enumerate(plants):
            self.table.insertRow(i)

            id_item = QTableWidgetItem()
            id_item.setData(Qt.UserRole, p["id"])
            self.table.setItem(i, 0, id_item)

            self.table.setItem(i, 1, QTableWidgetItem(p["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(p["species"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(p["last_watered"]))
            self.table.setItem(i, 4, QTableWidgetItem(str(p["frequency"])))

            days = (today - datetime.strptime(p["last_watered"], "%Y-%m-%d").date()).days
            if days <= p["frequency"]:
                status = QTableWidgetItem("Ок")
                status.setBackground(QColor(200, 255, 200))
            else:
                status = QTableWidgetItem(f"Просрочено на {days - p['frequency']} дн.")
                status.setBackground(QColor(255, 200, 200))
            self.table.setItem(i, 5, status)

        self.table.setColumnHidden(0, True)

    def _update_needing_water_status(self):
        needing = self.db.get_plants_needing_water()
        if not needing:
            self.lbl_needing_water.setText("Все растения политы.")
            self.lbl_needing_water.setStyleSheet("background-color: #C8E6C9; padding: 8px; border-radius: 6px; color: #1B5E20;")
        else:
            names = [f"{p['name']} (+{p['days_overdue']} дн.)" for p in needing[:3]]
            text = f"Требуют полива: {', '.join(names)}"
            if len(needing) > 3:
                text += f" и ещё {len(needing) - 3}..."
            self.lbl_needing_water.setText(text)
            self.lbl_needing_water.setStyleSheet("background-color: #FFCDD2; padding: 8px; border-radius: 6px; color: #B71C1C;")

    def _clear_form(self):
        self.le_name.clear()
        self.le_species.clear()
        self.de_watered.setDate(QDate(2026, 7, 4))
        self.spin_frequency.setValue(7)
        self.te_notes.clear()
        self.current_image_path = ""
        self.current_plant_id = None
        self._clear_image_display()
        self.table.clearSelection()

    def _get_selected_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите строку.")
            return None
        return selected[0].row()

    def closeEvent(self, event):
        if QMessageBox.question(self, "Выход", "Вы уверены?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()
