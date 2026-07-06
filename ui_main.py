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

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        lbl_title = QLabel("Мои растения")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(lbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Название", "Вид", "Последний полив", "Период (дней)", "Статус"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        left_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_water = QPushButton("Отметить полив")
        self.btn_refresh = QPushButton("Обновить")
        for btn in [self.btn_add, self.btn_edit, self.btn_delete,
                    self.btn_water, self.btn_refresh]:
            btn_layout.addWidget(btn)
        left_layout.addLayout(btn_layout)

        self.lbl_needing_water = QLabel("Нет растений, требующих полива")
        self.lbl_needing_water.setStyleSheet(
            "background-color: #fff3cd; padding: 8px; border-radius: 6px;"
        )
        left_layout.addWidget(self.lbl_needing_water)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        lbl_form_title = QLabel("Информация о растении")
        lbl_form_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(lbl_form_title)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)

        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("Например: Монстера")
        self.le_species = QLineEdit()
        self.le_species.setPlaceholderText("Например: Monstera deliciosa")
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

        form_layout.addRow("Название:", self.le_name)
        form_layout.addRow("Вид:", self.le_species)
        form_layout.addRow("Последний полив:", self.de_watered)
        form_layout.addRow("Период полива:", self.spin_frequency)
        form_layout.addRow("Заметки:", self.te_notes)

        right_layout.addWidget(form_widget)

        self.lbl_image = QLabel("Фото растения")
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setMinimumHeight(180)
        self.lbl_image.setStyleSheet("""
            background-color: #f5f5f5;
            border: 2px dashed #bbb;
            border-radius: 8px;
            font-size: 14px;
        """)
        right_layout.addWidget(self.lbl_image)

        img_btn_layout = QHBoxLayout()
        self.btn_load_img = QPushButton("Загрузить фото")
        self.btn_clear_img = QPushButton("Удалить фото")
        img_btn_layout.addWidget(self.btn_load_img)
        img_btn_layout.addWidget(self.btn_clear_img)
        right_layout.addLayout(img_btn_layout)

        action_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_clear = QPushButton("Очистить форму")
        action_layout.addWidget(self.btn_save)
        action_layout.addWidget(self.btn_clear)
        right_layout.addLayout(action_layout)

        right_layout.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f4f8; }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton#btn_delete {
                background-color: #dc3545;
            }
            QPushButton#btn_delete:hover {
                background-color: #c82333;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
                border-radius: 8px;
            }
            QTableWidget::item:selected {
                background-color: #90caf9;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QLineEdit, QTextEdit, QDateEdit, QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QSpinBox:focus {
                border-color: #4CAF50;
            }
            QLabel { color: #333; }
            QFormLayout { spacing: 12px; }
        """)

    def _bind_signals(self):
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_water.clicked.connect(self._on_water_plant)
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
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите растение для редактирования.")
            return

        row = selected[0].row()
        plant_id = self.table.item(row, 0).data(Qt.UserRole)

        plant = self.db.get_plant_by_id(plant_id)
        if plant:
            self.current_plant_id = plant_id
            self.le_name.setText(plant["name"])
            self.le_species.setText(plant["species"] or "")
            self.de_watered.setDate(QDate.fromString(plant["last_watered"], "yyyy-MM-dd"))
            self.spin_frequency.setValue(plant["frequency"])
            self.te_notes.setText(plant["notes"] or "")
            self.current_image_path = plant["image_path"] or ""
            if self.current_image_path:
                self._load_and_display_image(self.current_image_path)
            else:
                self._clear_image_display()

    def _on_delete(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите растение для удаления.")
            return

        row = selected[0].row()
        plant_name = self.table.item(row, 1).text()
        plant_id = self.table.item(row, 0).data(Qt.UserRole)

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить растение '{plant_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_plant(plant_id)
                self._refresh_table()
                self._clear_form()
                self._update_needing_water_status()
                QMessageBox.information(self, "Успех", f"Растение '{plant_name}' удалено.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить:\n{e}")

    def _on_water_plant(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите растение для отметки полива.")
            return

        row = selected[0].row()
        plant_id = self.table.item(row, 0).data(Qt.UserRole)
        plant_name = self.table.item(row, 1).text()

        self.db.update_watering_date(plant_id)
        self._refresh_table()
        self._update_needing_water_status()
        QMessageBox.information(self, "Успех", f"Полив для '{plant_name}' отмечен.")

    def _on_refresh(self):
        self._refresh_table()
        self._update_needing_water_status()
        QMessageBox.information(self, "Обновлено", "Данные обновлены.")

    def _on_select_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return

        row = selected[0].row()
        plant_id = self.table.item(row, 0).data(Qt.UserRole)

        plant = self.db.get_plant_by_id(plant_id)
        if plant:
            self.current_plant_id = plant_id
            self.le_name.setText(plant["name"])
            self.le_species.setText(plant["species"] or "")
            self.de_watered.setDate(QDate.fromString(plant["last_watered"], "yyyy-MM-dd"))
            self.spin_frequency.setValue(plant["frequency"])
            self.te_notes.setText(plant["notes"] or "")
            self.current_image_path = plant["image_path"] or ""
            if self.current_image_path:
                self._load_and_display_image(self.current_image_path)
            else:
                self._clear_image_display()

    def _on_load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото растения", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not path:
            return
        self.current_image_path = path
        self._load_and_display_image(path)

    def _load_and_display_image(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            max_size = (240, 240)
            img.thumbnail(max_size, Image.LANCZOS)
            data = img.tobytes("raw", "RGBA")
            qt_img = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qt_img)
            self.lbl_image.setPixmap(pixmap)
            self.lbl_image.setScaledContents(True)
            self.lbl_image.setStyleSheet("border: 2px solid #4CAF50; border-radius: 8px;")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение:\n{e}")
            self._clear_image_display()

    def _on_clear_image(self):
        self.current_image_path = ""
        self._clear_image_display()

    def _clear_image_display(self):
        self.lbl_image.setText("Фото растения")
        self.lbl_image.setPixmap(QPixmap())
        self.lbl_image.setStyleSheet("""
            background-color: #f5f5f5;
            border: 2px dashed #bbb;
            border-radius: 8px;
            font-size: 14px;
        """)

    def _on_save(self):
        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка валидации", "Название растения обязательно.")
            self.le_name.setFocus()
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
                msg = f"Растение '{name}' обновлено."
            else:
                new_id = self.db.insert_plant(data)
                self.current_plant_id = new_id
                msg = f"Растение '{name}' добавлено."

            self._refresh_table()
            self._clear_form()
            self._update_needing_water_status()
            QMessageBox.information(self, "Успех", msg)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные:\n{e}")

    def _refresh_table(self):
        self.table.setRowCount(0)
        plants = self.db.get_all()
        today = datetime.now().date()

        for i, plant in enumerate(plants):
            self.table.insertRow(i)

            id_item = QTableWidgetItem()
            id_item.setData(Qt.UserRole, plant["id"])
            self.table.setItem(i, 0, id_item)

            self.table.setItem(i, 1, QTableWidgetItem(plant["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(plant["species"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(plant["last_watered"]))
            self.table.setItem(i, 4, QTableWidgetItem(str(plant["frequency"])))

            last_watered = datetime.strptime(plant["last_watered"], "%Y-%m-%d").date()
            days_passed = (today - last_watered).days

            if days_passed <= plant["frequency"]:
                status = "Ок"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(QColor(200, 255, 200))
            else:
                overdue = days_passed - plant["frequency"]
                status = f"Просрочено на {overdue} дн."
                status_item = QTableWidgetItem(status)
                status_item.setBackground(QColor(255, 200, 200))

            self.table.setItem(i, 5, status_item)

        self.table.setColumnHidden(0, True)

    def _update_needing_water_status(self):
        needing = self.db.get_plants_needing_water()
        if not needing:
            self.lbl_needing_water.setText("Все растения политы.")
            self.lbl_needing_water.setStyleSheet(
                "background-color: #d4edda; padding: 8px; border-radius: 6px;"
            )
        else:
            names = [f"{p['name']} (+{p['days_overdue']} дн.)" for p in needing[:3]]
            text = f"Требуют полива: {', '.join(names)}"
            if len(needing) > 3:
                text += f" и ещё {len(needing) - 3}..."
            self.lbl_needing_water.setText(text)
            self.lbl_needing_water.setStyleSheet(
                "background-color: #f8d7da; padding: 8px; border-radius: 6px;"
            )

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

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()