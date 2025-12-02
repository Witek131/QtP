import sys
import json
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QComboBox, QDateEdit, QListWidget, QMessageBox,
                             QTabWidget, QGroupBox, QFormLayout, QSpinBox,
                             QDialog, QDialogButtonBox, QTextEdit, QFileDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPalette, QColor


class SubjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить/Редактировать предмет")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.subject_combo = QComboBox()
        self.subject_combo.setEditable(True)
        subjects = ["Русский язык", "Алгебра", "Информатика", "Геометрия",
                    "География", "История", "Обществознание", "Физика",
                    "Химия", "Биология", "Английский язык", "Литература"]
        self.subject_combo.addItems(subjects)
        form_layout.addRow("Предмет:", self.subject_combo)

        self.rate_2 = QSpinBox()
        self.rate_2.setRange(-100, 100)
        self.rate_2.setValue(-10)
        form_layout.addRow("За 2:", self.rate_2)

        self.rate_3 = QSpinBox()
        self.rate_3.setRange(-100, 100)
        self.rate_3.setValue(0)
        form_layout.addRow("За 3:", self.rate_3)

        self.rate_4 = QSpinBox()
        self.rate_4.setRange(-100, 100)
        self.rate_4.setValue(10)
        form_layout.addRow("За 4:", self.rate_4)

        self.rate_5 = QSpinBox()
        self.rate_5.setRange(-100, 100)
        self.rate_5.setValue(20)
        form_layout.addRow("За 5:", self.rate_5)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class GradeDialog(QDialog):
    def __init__(self, subjects, parent=None):
        super().__init__(parent)
        self.subjects = subjects
        self.setWindowTitle("Добавить оценку")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.subject_combo = QComboBox()
        self.update_subjects()
        form_layout.addRow("Предмет:", self.subject_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Дата:", self.date_edit)

        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["2", "3", "4", "5"])
        form_layout.addRow("Оценка:", self.grade_combo)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_subjects(self):
        self.subject_combo.clear()
        for subject in self.subjects.keys():
            self.subject_combo.addItem(subject)


class DataManager:
    def __init__(self):
        # Используем абсолютные пути
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(current_dir, "grade_counter_data.json")
        self.backup_file = os.path.join(current_dir, "grade_counter_backup.json")
        self.load_data()

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.subjects = data.get('subjects', {})
                    self.grades = data.get('grades', [])
                    self.base_rate = data.get('base_rate', 0)
            else:
                self.subjects = {}
                self.grades = []
                self.base_rate = 0
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            self.subjects = {}
            self.grades = []
            self.base_rate = 0

    def save_data(self):
        try:
            data = {
                'subjects': self.subjects,
                'grades': self.grades,
                'base_rate': self.base_rate
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.setWindowTitle("GradeCounter")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Заголовок
        title = QLabel("GradeCounter")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Вкладки
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Главная вкладка
        main_tab = QWidget()
        tabs.addTab(main_tab, "Главная")
        self.setup_main_tab(main_tab)

        # Предметы вкладка
        subjects_tab = QWidget()
        tabs.addTab(subjects_tab, "Предметы")
        self.setup_subjects_tab(subjects_tab)

        # Оценки вкладка
        grades_tab = QWidget()
        tabs.addTab(grades_tab, "Оценки")
        self.setup_grades_tab(grades_tab)

    def setup_main_tab(self, parent):
        layout = QVBoxLayout(parent)

        # Заработок
        earnings_group = QGroupBox("Сколько я заработал?")
        earnings_layout = QVBoxLayout(earnings_group)

        self.earnings_label = QLabel("0 руб.")
        self.earnings_label.setAlignment(Qt.AlignCenter)
        self.earnings_label.setFont(QFont("Arial", 20, QFont.Bold))
        earnings_layout.addWidget(self.earnings_label)

        buttons_layout = QHBoxLayout()

        week_btn = QPushButton("За неделю")
        week_btn.clicked.connect(lambda: self.calculate_earnings('week'))
        buttons_layout.addWidget(week_btn)

        month_btn = QPushButton("За месяц")
        month_btn.clicked.connect(lambda: self.calculate_earnings('month'))
        buttons_layout.addWidget(month_btn)

        year_btn = QPushButton("За год")
        year_btn.clicked.connect(lambda: self.calculate_earnings('year'))
        buttons_layout.addWidget(year_btn)

        earnings_layout.addLayout(buttons_layout)
        layout.addWidget(earnings_group)

        layout.addStretch()

    def setup_subjects_tab(self, parent):
        layout = QVBoxLayout(parent)

        add_subject_btn = QPushButton("Добавить предмет")
        add_subject_btn.clicked.connect(self.add_subject)
        layout.addWidget(add_subject_btn)

        self.subjects_list = QListWidget()
        self.update_subjects_list()
        layout.addWidget(self.subjects_list)

    def setup_grades_tab(self, parent):
        layout = QVBoxLayout(parent)

        add_grade_btn = QPushButton("Добавить оценку")
        add_grade_btn.clicked.connect(self.add_grade)
        layout.addWidget(add_grade_btn)

        self.grades_list = QListWidget()
        self.update_grades_list()
        layout.addWidget(self.grades_list)

    def add_subject(self):
        dialog = SubjectDialog(self)
        if dialog.exec_():
            QMessageBox.information(self, "Успех", "Предмет добавлен")

    def add_grade(self):
        if not self.data_manager.subjects:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте предметы")
            return

        dialog = GradeDialog(self.data_manager.subjects, self)
        if dialog.exec_():
            QMessageBox.information(self, "Успех", "Оценка добавлена")

    def update_subjects_list(self):
        self.subjects_list.clear()
        self.subjects_list.addItem("Математика - 2:-10р, 3:0р, 4:10р, 5:20р")
        self.subjects_list.addItem("Русский язык - 2:-5р, 3:0р, 4:15р, 5:25р")

    def update_grades_list(self):
        self.grades_list.clear()
        self.grades_list.addItem("2024-01-15 - Математика - 5")
        self.grades_list.addItem("2024-01-16 - Русский язык - 4")

    def calculate_earnings(self, period):
        earnings = {"week": 150, "month": 650, "year": 2500}
        self.earnings_label.setText(f"{earnings[period]} руб.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
