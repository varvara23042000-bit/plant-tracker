import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QSplitter, QDateEdit,
    QSpinBox, QTextEdit, QShortcut
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap, QImage, QColor, QKeySequence

from PIL import Image
import database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Трекер комнатных растений")
        self.resize(1100, 700)
        self.setMinimumSize(900, 550)

        self.db = database.DatabaseManager()
        self.image_path = ""
        self.edit_id = None

        self._setup()
        self._refresh()
        self._update_status()

    def _setup(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        layout = QHBoxLayout(cw)

        left = QWidget()
        lv = QVBoxLayout(left)
        lv.addWidget(QLabel("Мои растения"))
        lv.addWidget(self._make_table())
        lv.addLayout(self._make_buttons())
        lv.addWidget(self._make_status())

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.addWidget(QLabel("Информация"))
        rv.addWidget(self._make_form())
        rv.addWidget(self._make_image())
        rv.addLayout(self._make_img_btns())
        rv.addLayout(self._make_action_btns())
        rv.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

        self.setStyleSheet("""
            QMainWindow { background-color: #E8F5E9; }
            QPushButton { background-color: #43A047; color: white; border: none;
                          padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton#del { background-color: #C62828; }
            QPushButton#del:hover { background-color: #B71C1C; }
            QTableWidget { background-color: white; alternate-background-color: #F1F8E9;
                           gridline-color: #A5D6A7; border-radius: 8px; }
            QTableWidget::item:selected { background-color: #81C784; color: white; }
            QHeaderView::section { background-color: #66BB6A; padding: 6px; border: none;
                                   font-weight: bold; color: white; }
            QLineEdit, QTextEdit, QDateEdit, QSpinBox {
                border: 1px solid #A5D6A7; border-radius: 6px; padding: 8px;
                background-color: white; }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QSpinBox:focus {
                border-color: #43A047; }
            QLabel { color: #1B5E20; }
            QSplitter::handle { background-color: #81C784; }
        """)

        self._bind()
        self._setup_shortcuts()

    def _make_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Вид", "Полив", "Период", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        return self.table

    def _make_buttons(self):
        layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_del = QPushButton("Удалить")
        self.btn_del.setObjectName("del")
        self.btn_water = QPushButton("Полив")
        self.btn_refresh = QPushButton("Обновить")
        for btn in [self.btn_add, self.btn_edit, self.btn_del, self.btn_water, self.btn_refresh]:
            layout.addWidget(btn)
        return layout

    def _make_status(self):
        self.status = QLabel("Нет растений, требующих полива")
        self.status.setStyleSheet("background-color: #C8E6C9; padding: 8px; border-radius: 6px; color: #1B5E20;")
        return self.status

    def _make_form(self):
        form = QWidget()
        layout = QFormLayout(form)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Монстера")
        self.species = QLineEdit()
        self.species.setPlaceholderText("Monstera deliciosa")
        self.watered = QDateEdit()
        self.watered.setDate(QDate(2026, 7, 4))
        self.watered.setCalendarPopup(True)
        self.freq = QSpinBox()
        self.freq.setRange(1, 365)
        self.freq.setValue(7)
        self.freq.setSuffix(" дн.")
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Заметки по уходу...")

        layout.addRow("Название:", self.name)
        layout.addRow("Вид:", self.species)
        layout.addRow("Полив:", self.watered)
        layout.addRow("Период:", self.freq)
        layout.addRow("Заметки:", self.notes)
        return form

    def _make_image(self):
        self.image = QLabel("Фото растения")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumHeight(180)
        self.image.setStyleSheet("""
            background-color: #E8F5E9; border: 2px dashed #66BB6A;
            border-radius: 8px; font-size: 14px; color: #2E7D32;
        """)
        return self.image

    def _make_img_btns(self):
        layout = QHBoxLayout()
        self.btn_load = QPushButton("Загрузить фото")
        self.btn_clear_img = QPushButton("Удалить фото")
        layout.addWidget(self.btn_load)
        layout.addWidget(self.btn_clear_img)
        return layout

    def _make_action_btns(self):
        layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_clear = QPushButton("Очистить")
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_clear)
        return layout

    def _bind(self):
        self.btn_add.clicked.connect(lambda: (self._clear(), setattr(self, 'edit_id', None), self.name.setFocus()))
        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)
        self.btn_water.clicked.connect(self._water)
        self.btn_refresh.clicked.connect(self._refresh)
        self.btn_load.clicked.connect(self._load_image)
        self.btn_clear_img.clicked.connect(lambda: (setattr(self, 'image_path', ''), self._clear_image()))
        self.btn_save.clicked.connect(self._save)
        self.btn_clear.clicked.connect(self._clear)
        self.table.itemSelectionChanged.connect(self._select)

    def _setup_shortcuts(self):
        # Ctrl+N → Добавить
        shortcut_add = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_add.activated.connect(lambda: (self._clear(), setattr(self, 'edit_id', None), self.name.setFocus()))

        # Ctrl+S → Сохранить
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self._save)

        # Delete → Удалить
        shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        shortcut_delete.activated.connect(self._delete)

        # Ctrl+R → Обновить
        shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_refresh.activated.connect(self._refresh)

        # Ctrl+W → Отметить полив
        shortcut_water = QShortcut(QKeySequence("Ctrl+W"), self)
        shortcut_water.activated.connect(self._water)

        # Escape → Очистить форму
        shortcut_clear = QShortcut(QKeySequence("Escape"), self)
        shortcut_clear.activated.connect(self._clear)

    def _edit(self):
        row = self._selected()
        if row is None:
            return
        p = self.db.get_by_id(self.table.item(row, 0).data(Qt.UserRole))
        if p:
            self.edit_id = p["id"]
            self._fill(p)

    def _delete(self):
        row = self._selected()
        if row is None:
            return
        name = self.table.item(row, 1).text()
        if QMessageBox.question(self, "Удаление", f"Удалить '{name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete(self.table.item(row, 0).data(Qt.UserRole))
            self._refresh()
            self._clear()

    def _water(self):
        row = self._selected()
        if row is None:
            return
        self.db.water(self.table.item(row, 0).data(Qt.UserRole))
        self._refresh()
        QMessageBox.information(self, "Успех", "Полив отмечен")

    def _select(self):
        row = self._selected()
        if row is not None:
            p = self.db.get_by_id(self.table.item(row, 0).data(Qt.UserRole))
            if p:
                self.edit_id = p["id"]
                self._fill(p)

    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.image_path = path
            self._display_image(path)

    def _display_image(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((240, 240), Image.LANCZOS)
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            self.image.setPixmap(QPixmap.fromImage(qimg))
            self.image.setScaledContents(True)
            self.image.setStyleSheet("border: 2px solid #43A047; border-radius: 8px;")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить фото:\n{e}")
            self._clear_image()

    def _clear_image(self):
        self.image.setText("Фото растения")
        self.image.setPixmap(QPixmap())
        self.image.setStyleSheet("""
            background-color: #E8F5E9; border: 2px dashed #66BB6A;
            border-radius: 8px; font-size: 14px; color: #2E7D32;
        """)

    def _save(self):
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название обязательно")
            return

        data = {
            "name": name,
            "species": self.species.text().strip(),
            "last_watered": self.watered.date().toString("yyyy-MM-dd"),
            "frequency": self.freq.value(),
            "notes": self.notes.toPlainText().strip(),
            "image_path": self.image_path
        }

        try:
            if self.edit_id:
                data["id"] = self.edit_id
                self.db.update(data)
                msg = f"'{name}' обновлено"
            else:
                self.edit_id = self.db.insert(data)
                msg = f"'{name}' добавлено"
            self._refresh()
            self._clear()
            QMessageBox.information(self, "Успех", msg)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def _refresh(self):
        self.table.setRowCount(0)
        today = datetime.now().date()

        for i, p in enumerate(self.db.get_all()):
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
                item = QTableWidgetItem("Ок")
                item.setBackground(QColor(200, 255, 200))
            else:
                item = QTableWidgetItem(f"Просрочка {days - p['frequency']} дн.")
                item.setBackground(QColor(255, 200, 200))
            self.table.setItem(i, 5, item)

        self.table.setColumnHidden(0, True)
        self._update_status()

    def _update_status(self):
        needing = self.db.needing_water()
        if not needing:
            self.status.setText("Все растения политы")
            self.status.setStyleSheet("background-color: #C8E6C9; padding: 8px; border-radius: 6px; color: #1B5E20;")
        else:
            names = [f"{p['name']} (+{p['overdue']} дн.)" for p in needing[:3]]
            text = f"Требуют полива: {', '.join(names)}"
            if len(needing) > 3:
                text += f" и ещё {len(needing) - 3}..."
            self.status.setText(text)
            self.status.setStyleSheet("background-color: #FFCDD2; padding: 8px; border-radius: 6px; color: #B71C1C;")

    def _fill(self, p):
        self.name.setText(p["name"])
        self.species.setText(p["species"] or "")
        self.watered.setDate(QDate.fromString(p["last_watered"], "yyyy-MM-dd"))
        self.freq.setValue(p["frequency"])
        self.notes.setText(p["notes"] or "")
        self.image_path = p["image_path"] or ""
        if self.image_path:
            self._display_image(self.image_path)
        else:
            self._clear_image()

    def _clear(self):
        self.name.clear()
        self.species.clear()
        self.watered.setDate(QDate(2026, 7, 4))
        self.freq.setValue(7)
        self.notes.clear()
        self.image_path = ""
        self.edit_id = None
        self._clear_image()
        self.table.clearSelection()

    def _selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Внимание", "Выберите строку")
            return None
        return rows[0].row()

    def closeEvent(self, event):
        if QMessageBox.question(self, "Выход", "Вы уверены?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()
