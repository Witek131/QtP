import sys, csv, sqlite3, datetime, shutil, os
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

DB_NAME, LOG_FILE, BACKUP_DIR = "tasks.db", "activity.log", "backups"


def log(message):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception:
        pass


class TaskDB:
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_backup_dir()

    def create_backup_dir(self):
        if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)

    def connect(self):
        try:
            self.conn = sqlite3.connect(DB_NAME)
            self.create_table()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка БД", f"Не удалось подключиться: {e}")

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL, description TEXT, priority TEXT,
                status TEXT, created TEXT, deadline TEXT, reminder TEXT
            )""")
        self.conn.commit()

    def add_task(self, title, description, priority, status, deadline="", reminder=""):
        try:
            created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            self.conn.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?)",
                              (None, title, description, priority, status, created, deadline, reminder))
            self.conn.commit()
            log(f"Добавлена: {title}")
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось добавить: {e}")
            return False

    def get_tasks(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM tasks")
            return cur.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось загрузить: {e}")
            return []

    def get_tasks_by_date(self, date):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE deadline = ?", (date,))
            return cur.fetchall()
        except sqlite3.Error:
            return []

    def update_task(self, task_id, title, description, priority, status, deadline="", reminder=""):
        try:
            self.conn.execute("""UPDATE tasks SET title=?, description=?, priority=?, 
                status=?, deadline=?, reminder=? WHERE id=?""",
                              (title, description, priority, status, deadline, reminder, task_id))
            self.conn.commit()
            log(f"Изменена ID {task_id}")
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось обновить: {e}")
            return False

    def delete_task(self, task_id):
        try:
            self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self.conn.commit()
            log(f"Удалена ID {task_id}")
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось удалить: {e}")
            return False


class StatsWindow(QDialog):
    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Статистика")
        self.resize(400, 300)
        self.setModal(True)
        layout = QVBoxLayout(self)

        total, done = len(tasks), sum(1 for t in tasks if t[4] == "Готово")
        high = sum(1 for t in tasks if t[3] == "Высокий")
        mid = sum(1 for t in tasks if t[3] == "Средний")
        low = sum(1 for t in tasks if t[3] == "Низкий")
        today = datetime.datetime.now().date()
        overdue = sum(1 for t in tasks if
                      t[6] and datetime.datetime.strptime(t[6], '%Y-%m-%d').date() < today and t[4] != "Готово")

        stats_group = QGroupBox("Общая статистика")
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(QLabel(f"Всего: {total}"))
        stats_layout.addWidget(QLabel(f"Выполнено: {done}"))
        stats_layout.addWidget(QLabel(f"В процессе: {total - done}"))
        stats_layout.addWidget(QLabel(f"Просрочено: {overdue}"))
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        priority_group = QGroupBox("Приоритеты")
        priority_layout = QVBoxLayout()
        priority_layout.addWidget(QLabel(f"Высокий: {high}"))
        priority_layout.addWidget(QLabel(f"Средний: {mid}"))
        priority_layout.addWidget(QLabel(f"Низкий: {low}"))
        priority_group.setLayout(priority_layout)
        layout.addWidget(priority_group)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class EditTaskDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование" if data else "Добавление")
        self.setModal(True)
        self.resize(500, 400)
        self.data, self.valid = data, False

        layout = QVBoxLayout(self)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название (обязательно)")
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        self.priority_choice = QComboBox()
        self.priority_choice.addItems(["Низкий", "Средний", "Высокий"])
        self.status_choice = QComboBox()
        self.status_choice.addItems(["В процессе", "Готово"])

        deadline_layout = QHBoxLayout()
        self.deadline_check = QCheckBox("Дедлайн")
        self.deadline_input = QDateEdit()
        self.deadline_input.setDate(QDate.currentDate().addDays(7))
        self.deadline_input.setEnabled(False)
        self.deadline_check.toggled.connect(self.deadline_input.setEnabled)
        deadline_layout.addWidget(self.deadline_check)
        deadline_layout.addWidget(self.deadline_input)

        reminder_layout = QHBoxLayout()
        self.reminder_check = QCheckBox("Напоминание")
        self.reminder_input = QDateTimeEdit()
        self.reminder_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.reminder_input.setEnabled(False)
        self.reminder_check.toggled.connect(self.reminder_input.setEnabled)
        reminder_layout.addWidget(self.reminder_check)
        reminder_layout.addWidget(self.reminder_input)

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red;")

        layout.addWidget(QLabel("Название*:"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(self.desc_input)
        layout.addWidget(QLabel("Приоритет:"))
        layout.addWidget(self.priority_choice)
        layout.addWidget(QLabel("Статус:"))
        layout.addWidget(self.status_choice)
        layout.addWidget(QLabel("Дедлайн:"))
        layout.addLayout(deadline_layout)
        layout.addWidget(QLabel("Напоминание:"))
        layout.addLayout(reminder_layout)
        layout.addWidget(self.validation_label)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setEnabled(False)
        cancel = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(cancel)
        layout.addLayout(btns)

        self.title_input.textChanged.connect(self.validate_input)
        if data:
            self.title_input.setText(data[1])
            self.desc_input.setText(data[2])
            self.priority_choice.setCurrentText(data[3])
            self.status_choice.setCurrentText(data[4])
            if data[6]:
                self.deadline_input.setDate(QDate.fromString(data[6], 'yyyy-MM-dd'))
                self.deadline_check.setChecked(True)
            if data[7]:
                self.reminder_input.setDateTime(QDateTime.fromString(data[7], 'yyyy-MM-dd HH:mm'))
                self.reminder_check.setChecked(True)

        self.save_btn.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        self.validate_input()

    def validate_input(self):
        title = self.title_input.text().strip()
        if not title:
            self.validation_label.setText("Название не может быть пустым")
        elif len(title) < 2:
            self.validation_label.setText("Название слишком короткое")
        else:
            self.validation_label.setText("")
        self.valid = bool(title and len(title) >= 2)
        self.save_btn.setEnabled(self.valid)

    def get_data(self):
        deadline = self.deadline_input.date().toString('yyyy-MM-dd') if self.deadline_check.isChecked() else ""
        reminder = self.reminder_input.dateTime().toString(
            'yyyy-MM-dd HH:mm') if self.reminder_check.isChecked() else ""
        return (self.title_input.text().strip(), self.desc_input.toPlainText().strip(),
                self.priority_choice.currentText(), self.status_choice.currentText(), deadline, reminder)


class CalendarWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db, self.date_tasks = db, {}
        self.main_window = parent  # Сохраняем ссылку на главное окно
        self.setup_ui()
        self.load_tasks_to_calendar()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.tasks_list = QListWidget()
        btn_layout = QHBoxLayout()
        self.add_to_date_btn = QPushButton("Добавить на дату")
        self.view_task_btn = QPushButton("Просмотреть")
        self.mark_done_btn = QPushButton("Выполнено")

        layout.addWidget(QLabel("Календарь:"))
        layout.addWidget(self.calendar)
        layout.addWidget(QLabel("Задачи на дату:"))
        layout.addWidget(self.tasks_list)
        btn_layout.addWidget(self.add_to_date_btn)
        btn_layout.addWidget(self.view_task_btn)
        btn_layout.addWidget(self.mark_done_btn)
        layout.addLayout(btn_layout)

        self.calendar.selectionChanged.connect(self.on_date_selected)
        self.add_to_date_btn.clicked.connect(self.add_task_to_date)
        self.view_task_btn.clicked.connect(self.view_selected_task)
        self.mark_done_btn.clicked.connect(self.mark_task_done)
        self.tasks_list.itemDoubleClicked.connect(self.view_task_from_list)

    def load_tasks_to_calendar(self):
        tasks = self.db.get_tasks()
        today = QDate.currentDate()
        for task in tasks:
            if task[6]:
                try:
                    task_date = QDate.fromString(task[6], 'yyyy-MM-dd')
                    fmt = QTextCharFormat()
                    if task[4] == "Готово":
                        fmt.setBackground(QColor(200, 255, 200))
                    elif task_date < today:
                        fmt.setBackground(QColor(255, 200, 200))
                    else:
                        fmt.setBackground(QColor(255, 255, 200))
                    self.calendar.setDateTextFormat(task_date, fmt)
                except:
                    continue
        self.on_date_selected()

    def on_date_selected(self):
        selected_date = self.calendar.selectedDate().toString('yyyy-MM-dd')
        tasks = self.db.get_tasks_by_date(selected_date)
        self.tasks_list.clear()
        self.date_tasks = {}
        for task in tasks:
            status_icon = "✅" if task[4] == "Готово" else "⏳"
            priority_icon = "🔴" if task[3] == "Высокий" else "🟡" if task[3] == "Средний" else "🟢"
            item = QListWidgetItem(f"{status_icon} {priority_icon} {task[1]}")
            item.setData(Qt.ItemDataRole.UserRole, task[0])
            self.tasks_list.addItem(item)
            self.date_tasks[task[0]] = task

    def add_task_to_date(self):
        selected_date = self.calendar.selectedDate()
        dlg = EditTaskDialog(self)
        dlg.deadline_check.setChecked(True)
        dlg.deadline_input.setDate(selected_date)
        if dlg.exec():
            t, d, p, s, deadline, reminder = dlg.get_data()
            if self.db.add_task(t, d, p, s, deadline, reminder):
                # Обновляем и календарь, и главное окно
                self.load_tasks_to_calendar()
                if self.main_window:
                    self.main_window.load_tasks()

    def view_selected_task(self):
        if self.tasks_list.currentItem(): self.view_task_from_list(self.tasks_list.currentItem())

    def view_task_from_list(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        task = self.date_tasks.get(task_id)
        if task:
            dlg = EditTaskDialog(self, data=task)
            if dlg.exec():
                t, d, p, s, deadline, reminder = dlg.get_data()
                if self.db.update_task(task_id, t, d, p, s, deadline, reminder):
                    self.load_tasks_to_calendar()
                    if self.main_window:
                        self.main_window.load_tasks()

    def mark_task_done(self):
        current_item = self.tasks_list.currentItem()
        if current_item:
            task_id = current_item.data(Qt.ItemDataRole.UserRole)
            task = self.date_tasks.get(task_id)
            if task and task[4] != "Готово":
                if QMessageBox.question(self, "Подтверждение",
                                        "Отметить как выполненную?") == QMessageBox.StandardButton.Yes:
                    if self.db.update_task(task_id, task[1], task[2], task[3], "Готово", task[6],
                                           task[7] if len(task) > 7 else ""):
                        self.load_tasks_to_calendar()
                        if self.main_window:
                            self.main_window.load_tasks()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Менеджер задач")
        self.resize(1400, 800)
        self.db = TaskDB()
        self.setup_ui()
        self.setup_shortcuts()
        self.load_tasks()
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(30000)
        self.shown_reminders = set()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget, right_widget = QWidget(), QWidget()
        left_layout, right_layout = QVBoxLayout(left_widget), QVBoxLayout(right_widget)

        self.calendar_widget = CalendarWidget(self.db, self)  # Передаем self как родителя
        right_layout.addWidget(self.calendar_widget)

        control = QHBoxLayout()

        # Создаем кнопки с английскими именами атрибутов
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить")
        self.stats_btn = QPushButton("Статистика")
        self.backup_btn = QPushButton("Бэкап")
        self.restore_btn = QPushButton("Восстановить")
        self.export_btn = QPushButton("Экспорт")
        self.import_btn = QPushButton("Импорт")

        buttons = [self.add_btn, self.edit_btn, self.delete_btn, self.stats_btn,
                   self.backup_btn, self.restore_btn, self.export_btn, self.import_btn]

        for btn in buttons:
            btn.setFixedHeight(35)
            control.addWidget(btn)

        left_layout.addLayout(control)

        filter_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["Все приоритеты", "Низкий", "Средний", "Высокий"])
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все статусы", "В процессе", "Готово"])
        self.deadline_filter = QComboBox()
        self.deadline_filter.addItems(["Все задачи", "Просроченные", "Сегодня", "На этой неделе"])

        for label, widget in [("Поиск:", self.search_input), ("Приоритет:", self.priority_filter),
                              ("Статус:", self.status_filter), ("Дедлайн:", self.deadline_filter)]:
            filter_bar.addWidget(QLabel(label))
            filter_bar.addWidget(widget)
        left_layout.addLayout(filter_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Название", "Описание", "Приоритет", "Статус", "Создано", "Дедлайн", "Напоминание"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for i in [0, 3, 4, 5, 6, 7]: header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        left_layout.addWidget(self.table)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([800, 400])

        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(splitter)
        self.connect_signals()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.add_task)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.edit_task)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.delete_task)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.search_input.setFocus)

    def connect_signals(self):
        self.add_btn.clicked.connect(self.add_task)
        self.edit_btn.clicked.connect(self.edit_task)
        self.delete_btn.clicked.connect(self.delete_task)
        self.stats_btn.clicked.connect(self.show_stats)
        self.backup_btn.clicked.connect(self.create_backup)
        self.restore_btn.clicked.connect(self.restore_backup)
        self.export_btn.clicked.connect(self.export_csv)
        self.import_btn.clicked.connect(self.import_csv)

        self.search_input.textChanged.connect(self.update_filters)
        self.priority_filter.currentTextChanged.connect(self.update_filters)
        self.status_filter.currentTextChanged.connect(self.update_filters)
        self.deadline_filter.currentTextChanged.connect(self.update_filters)

        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemSelectionChanged.connect(self.update_status_bar)

    def load_tasks(self):
        tasks = self.db.get_tasks()
        self.all_tasks = tasks
        self.apply_filters(tasks)
        # Обновляем календарь при каждой загрузке задач
        self.calendar_widget.load_tasks_to_calendar()

    def apply_filters(self, tasks):
        search = self.search_input.text().lower()
        p_filter = self.priority_filter.currentText()
        s_filter = self.status_filter.currentText()
        d_filter = self.deadline_filter.currentText()
        today = datetime.datetime.now().date()
        week_end = today + datetime.timedelta(days=7)

        filtered = []
        for t in tasks:
            if search and search not in t[1].lower() and search not in t[2].lower(): continue
            if p_filter != "Все приоритеты" and t[3] != p_filter: continue
            if s_filter != "Все статусы" and t[4] != s_filter: continue
            if d_filter != "Все задачи" and t[6]:
                try:
                    deadline = datetime.datetime.strptime(t[6], '%Y-%m-%d').date()
                    if d_filter == "Просроченные" and (deadline >= today or t[4] == "Готово"):
                        continue
                    elif d_filter == "Сегодня" and deadline != today:
                        continue
                    elif d_filter == "На этой неделе" and not (today <= deadline <= week_end):
                        continue
                except:
                    continue
            elif d_filter != "Все задачи" and not t[6]:
                continue
            filtered.append(t)
        self.fill_table(filtered)

    def update_filters(self):
        self.apply_filters(self.all_tasks)

    def fill_table(self, tasks):
        self.table.setRowCount(len(tasks))
        today = datetime.datetime.now().date()
        for row, task in enumerate(tasks):
            for col, value in enumerate(task):
                item = QTableWidgetItem(str(value))
                if col == 3:
                    if value == "Высокий":
                        item.setBackground(QColor(255, 200, 200))
                    elif value == "Средний":
                        item.setBackground(QColor(255, 255, 200))
                    else:
                        item.setBackground(QColor(200, 255, 200))
                elif col == 4 and value == "Готово":
                    item.setBackground(QColor(200, 255, 200))
                elif col == 6 and value:
                    try:
                        deadline = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                        if deadline < today and task[4] != "Готово":
                            item.setBackground(QColor(255, 150, 150))
                        elif (deadline - today).days <= 1 and task[4] != "Готово":
                            item.setBackground(QColor(255, 200, 150))
                    except:
                        pass
                self.table.setItem(row, col, item)
        self.update_status_bar()

    def update_status_bar(self):
        total, filtered = len(self.all_tasks), self.table.rowCount()
        selected = len(self.table.selectionModel().selectedRows())
        status_text = f"Всего: {total}"
        if total != filtered: status_text += f" (отфильтровано: {filtered})"
        if selected > 0: status_text += f" | Выбрано: {selected}"
        self.status_bar.showMessage(status_text)

    def add_task(self):
        dlg = EditTaskDialog(self)
        if dlg.exec():
            t, d, p, s, deadline, reminder = dlg.get_data()
            if self.db.add_task(t, d, p, s, deadline, reminder):
                self.load_tasks()

    def edit_task(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу")
            return
        task = [self.table.item(row, i).text() for i in range(8)]
        dlg = EditTaskDialog(self, data=task)
        if dlg.exec():
            t, d, p, s, deadline, reminder = dlg.get_data()
            if self.db.update_task(task[0], t, d, p, s, deadline, reminder):
                self.load_tasks()

    def delete_task(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу")
            return
        task_name = self.table.item(row, 1).text()
        if QMessageBox.question(self, "Подтверждение", f"Удалить '{task_name}'?") == QMessageBox.StandardButton.Yes:
            task_id = self.table.item(row, 0).text()
            if self.db.delete_task(task_id):
                self.load_tasks()

    def show_context_menu(self, position):
        menu = QMenu(self)
        actions = ["Редактировать", "Удалить", "Отметить выполненной", "В процессе"]
        for text in actions:
            menu.addAction(text)
        action = menu.exec(self.table.mapToGlobal(position))
        if action:
            if action.text() == "Редактировать":
                self.edit_task()
            elif action.text() == "Удалить":
                self.delete_task()
            elif action.text() == "Отметить выполненной":
                self.mark_task_status("Готово")
            elif action.text() == "В процессе":
                self.mark_task_status("В процессе")

    def mark_task_status(self, status):
        row = self.table.currentRow()
        if row < 0: return
        task_id = self.table.item(row, 0).text()
        task = [self.table.item(row, i).text() for i in range(8)]
        if self.db.update_task(task_id, task[1], task[2], task[3], status, task[6], task[7]):
            self.load_tasks()

    def create_backup(self):
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{BACKUP_DIR}/tasks_backup_{timestamp}.db"
            shutil.copy2(DB_NAME, backup_name)
            backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('tasks_backup_')])
            for old_backup in backups[:-5]: os.remove(f"{BACKUP_DIR}/{old_backup}")
            QMessageBox.information(self, "Успех", "Бэкап создан!")
        except:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать бэкап")

    def restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", BACKUP_DIR, "Database files (*.db)")
        if path and QMessageBox.question(self, "Подтверждение", "Продолжить?") == QMessageBox.StandardButton.Yes:
            try:
                self.db.conn.close()
                shutil.copy2(path, DB_NAME)
                self.db.connect()
                self.load_tasks()
                QMessageBox.information(self, "Успех", "Данные восстановлены!")
            except:
                QMessageBox.warning(self, "Ошибка", "Не удалось восстановить")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV",
                                              f"tasks_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                              "CSV files (*.csv)")
        if path:
            try:
                tasks = self.db.get_tasks()
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["ID", "Название", "Описание", "Приоритет", "Статус", "Создано", "Дедлайн", "Напоминание"])
                    writer.writerows(tasks)
                QMessageBox.information(self, "Успех", f"Экспортировано в {path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {e}")

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть CSV", "", "CSV files (*.csv)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader)
                    imported = 0
                    for row in reader:
                        if len(row) < 5: continue
                        title, desc, prior, stat, created = row[1:6]
                        deadline = row[6] if len(row) > 6 else ""
                        reminder = row[7] if len(row) > 7 else ""
                        if not title.strip(): continue
                        if prior not in ["Низкий", "Средний", "Высокий"]: prior = "Средний"
                        if stat not in ["В процессе", "Готово"]: stat = "В процессе"
                        self.db.conn.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?)",
                                             (None, title, desc, prior, stat, created, deadline, reminder))
                        imported += 1
                    self.db.conn.commit()
                self.load_tasks()
                QMessageBox.information(self, "Успех", f"Импортировано: {imported}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка импорта: {e}")

    def show_stats(self):
        tasks = self.db.get_tasks()
        stats = StatsWindow(tasks, self)
        stats.exec()

    def check_reminders(self):
        tasks = self.db.get_tasks()
        now = datetime.datetime.now()
        for task in tasks:
            if task[7]:
                try:
                    reminder_time = datetime.datetime.strptime(task[7], '%Y-%m-%d %H:%M')
                    if now >= reminder_time:
                        reminder_key = f"{task[0]}_{task[7]}"
                        if reminder_key not in self.shown_reminders:
                            self.show_reminder(task)
                            self.shown_reminders.add(reminder_key)
                except:
                    continue

    def show_reminder(self, task):
        msg = QMessageBox(self)
        msg.setWindowTitle("Напоминание")
        msg.setText(f"Напоминание:\n\n{task[1]}\n{task[2]}\nПриоритет: {task[3]}")
        msg.addButton("Отложить 5 мин", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Выполнено", QMessageBox.ButtonRole.YesRole)
        msg.addButton("Закрыть", QMessageBox.ButtonRole.RejectRole)
        result = msg.exec()
        if result == 0:
            new_reminder = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M')
            self.db.update_task(task[0], task[1], task[2], task[3], task[4], task[6], new_reminder)
        elif result == 1:
            self.db.update_task(task[0], task[1], task[2], task[3], "Готово", task[6], "")
            self.load_tasks()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec())