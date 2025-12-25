import sys
import mysql.connector
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget,
    QLineEdit, QPushButton, QToolBar, QLabel,QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
from datetime import datetime, timedelta

# ---------------- MYSQL CONNECTION ----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="final-project"
)
cursor = conn.cursor()

BASE_DATE = datetime(2000, 1, 1)  # base for storing seconds in DATETIME


def update_db(user_id, url, usage_seconds):
    now = datetime.now()

    cursor.execute(
        "SELECT current_usage FROM user_usage WHERE ul_id=%s AND url=%s",
        (user_id, url)
    )
    row = cursor.fetchone()

    if row:
        current_seconds = int((row[0] - BASE_DATE).total_seconds())
        new_seconds = current_seconds + usage_seconds
    else:
        new_seconds = usage_seconds

    new_usage_datetime = BASE_DATE + timedelta(seconds=new_seconds)

    cursor.execute(
        """
        INSERT INTO user_usage (ul_id, url, daily_limit, current_usage, last_reset)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            current_usage = VALUES(current_usage),
            last_reset = VALUES(last_reset)
        """,
        (
            user_id,
            url,
            BASE_DATE + timedelta(hours=24),
            new_usage_datetime,
            now
        )
    )
    conn.commit()


def check_limit(user_id, url):
    today = datetime.today().date()

    cursor.execute(
        "SELECT current_usage, daily_limit FROM user_usage "
        "WHERE ul_id=%s AND url=%s AND DATE(last_reset)=%s",
        (user_id, url, today)
    )
    row = cursor.fetchone()

    if not row:
        return True

    current_usage, daily_limit = row
    if not daily_limit:
        return True

    current_seconds = int((current_usage - BASE_DATE).total_seconds())
    limit_seconds = int((daily_limit - BASE_DATE).total_seconds())

    return current_seconds < limit_seconds


# ---------------- MINI BROWSER ----------------
class MiniBrowser(QMainWindow):
    def __init__(self, user_id=1):
        super().__init__()
        self.user_id = user_id

        self.setWindowTitle("ELVORA Browser")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.setCentralWidget(self.tabs)

        self.tab_data = {}
        self.current_tab_index = None

        # Toolbar
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        self.url_bar = QLineEdit()
        self.go_btn = QPushButton("Go")
        self.new_tab_btn = QPushButton("New Tab")

        self.navbar.addWidget(self.url_bar)
        self.navbar.addWidget(self.go_btn)
        self.navbar.addWidget(self.new_tab_btn)

        self.status = QLabel("Total Time: 0 sec")
        self.statusBar().addWidget(self.status)

        self.go_btn.clicked.connect(self.navigate)
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        self.tabs.currentChanged.connect(self.tab_changed)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.add_new_tab("https://www.google.com")

        # -------- 5 second sync timer --------
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_every_5_seconds)
        self.sync_timer.start(5000)
    
    def show_limit_message(self, url):
        QMessageBox.warning(
            self,
            "Daily Limit Reached",
            f"Daily usage limit for:\n\n{url}\n\nhas been reached.\nAccess is blocked for today."
        )
    # ---------------- TAB MANAGEMENT ----------------
    def add_new_tab(self, url=None):
        if not url:
            url = "https://www.google.com"

        if not check_limit(self.user_id, url):
            self.statusBar().showMessage("Daily limit reached. Access blocked.")
            self.show_limit_message(url)
            return

        browser = QWebEngineView()
        browser.setUrl(QUrl(url))

        index = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(index)

        self.tab_data[index] = {
            "url": url,
            "start_time": time.time(),
            "total_time": 0
        }
        self.current_tab_index = index

    def close_tab(self, index):
        self.update_current_tab_time()

        data = self.tab_data.get(index)
        if data:
            update_db(self.user_id, data["url"], int(data["total_time"]))

        self.tabs.removeTab(index)
        self.tab_data.pop(index, None)

    def tab_changed(self, index):
        self.update_current_tab_time()
        self.current_tab_index = index
        if index in self.tab_data:
            self.tab_data[index]["start_time"] = time.time()

    # ---------------- NAVIGATION ----------------
    def navigate(self):
        url = self.url_bar.text().strip()
        if not url:
            return

        if not url.startswith("http"):
            url = "https://" + url

        # 🚫 LIMIT CHECK
        if not check_limit(self.user_id, url):
            self.statusBar().showMessage("Daily limit reached. Access blocked.")
            self.show_limit_message(url)
            return  # ⛔ STOP HERE

        browser = self.tabs.currentWidget()
        browser.setUrl(QUrl(url))

        index = self.tabs.currentIndex()
        self.tab_data[index]["url"] = url
        self.tabs.setTabText(index, url[:15])

        url = self.url_bar.text().strip()
        if not url:
            return
        if not url.startswith("http"):
            url = "https://" + url

        if not check_limit(self.user_id, url):
            self.statusBar().showMessage(f"Daily limit reached for {url}")
            return

        browser = self.tabs.currentWidget()
        browser.setUrl(QUrl(url))

        index = self.tabs.currentIndex()
        self.tab_data[index]["url"] = url
        self.tabs.setTabText(index, url[:15])

    # ---------------- 5s SYNC ----------------
    def sync_every_5_seconds(self):
        if self.current_tab_index is None:
            return

        data = self.tab_data.get(self.current_tab_index)
        if not data:
            return

        now = time.time()
        elapsed = now - data["start_time"]

        if elapsed <= 0:
            return

        data["total_time"] += elapsed
        data["start_time"] = now

        update_db(self.user_id, data["url"], int(elapsed))
        self.update_total_time()

    # ---------------- TIME TRACKING ----------------
    def update_current_tab_time(self):
        if self.current_tab_index is None:
            return

        data = self.tab_data.get(self.current_tab_index)
        if not data:
            return

        now = time.time()
        elapsed = now - data["start_time"]

        data["total_time"] += elapsed
        data["start_time"] = now

        self.update_total_time()

    def update_total_time(self):
        total = sum(tab["total_time"] for tab in self.tab_data.values())
        self.status.setText(f"Total Time: {int(total)} sec")

    # ---------------- CLOSE APP ----------------
    def closeEvent(self, event):
        self.sync_timer.stop()
        self.update_current_tab_time()
        event.accept()


# ---------------- RUN APP ----------------
app = QApplication(sys.argv)
window = MiniBrowser(user_id=1)
window.show()
sys.exit(app.exec_())
