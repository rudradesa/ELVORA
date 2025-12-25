import sys
import mysql.connector
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QLineEdit, QPushButton, QToolBar, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from datetime import datetime, timedelta

# ---------------- MYSQL CONNECTION ----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",   # your MySQL password
    database="browser_db"
)
cursor = conn.cursor()

BASE_DATE = datetime(2000, 1, 1)  # For storing seconds in DATETIME column

# ---------------- DATABASE FUNCTIONS ----------------
def update_db(user_id, url, usage_seconds):
    today = datetime.today().date()
    
    # Check if a row exists for this URL and user today
    cursor.execute(
        "SELECT current_usage, last_reset FROM user_usage WHERE ul_id=%s AND url=%s",
        (user_id, url)
    )
    result = cursor.fetchone()

    usage_delta = timedelta(seconds=usage_seconds)
    now = datetime.now()

    if result:
        current_usage, last_reset = result

        # Reset if last_reset is not today
        if last_reset.date() < today:
            current_usage = BASE_DATE  # reset usage
            last_reset = now

        # Convert current_usage DATETIME to seconds
        if isinstance(current_usage, datetime):
            current_seconds = int((current_usage - BASE_DATE).total_seconds())
        else:
            current_seconds = 0

        new_seconds = current_seconds + usage_seconds
        new_usage_datetime = BASE_DATE + timedelta(seconds=new_seconds)

        cursor.execute(
            "UPDATE user_usage SET current_usage=%s, last_reset=%s WHERE ul_id=%s AND url=%s",
            (new_usage_datetime, now, user_id, url)
        )
    else:
        # Row does not exist → insert new
        new_usage_datetime = BASE_DATE + timedelta(seconds=usage_seconds)
        cursor.execute(
            "INSERT INTO user_usage (ul_id, url, current_usage, last_reset) VALUES (%s, %s, %s, %s)",
            (user_id, url, new_usage_datetime, now)
        )

    conn.commit()
def check_limit(user_id, url):
    today = datetime.today().date()
    cursor.execute(
        "SELECT current_usage, daily_limit FROM user_usage WHERE ul_id=%s AND url=%s AND DATE(last_reset)=%s",
        (user_id, url, today)
    )
    result = cursor.fetchone()
    if not result:
        return True  # No record → allow

    current_usage, daily_limit = result

    if not daily_limit:
        return True  # No limit set → allow

    # Convert DATETIME to seconds
    current_seconds = int((current_usage - BASE_DATE).total_seconds()) if current_usage else 0
    limit_seconds = int((daily_limit - BASE_DATE).total_seconds()) if daily_limit else 0

    return current_seconds < limit_seconds

# ---------------- MINI BROWSER CLASS ----------------
class MiniBrowser(QMainWindow):
    def __init__(self, user_id=1):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Mini Browser with Daily Limit Tracking")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.setCentralWidget(self.tabs)

        self.tab_data = {}  # tab_index -> {url, start_time, total_time}
        self.current_tab_index = None

        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter website URL")
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

    # ---------------- TAB MANAGEMENT ----------------
    def add_new_tab(self, url=None):
        if not url:
            url = "https://www.google.com"

        # Check daily limit
        if not check_limit(self.user_id, url):
            self.statusBar().showMessage(f"Daily limit reached for {url}. Cannot open for 24h.")
            return

        browser = QWebEngineView()
        browser.setUrl(QUrl(url))

        index = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(index)

        self.tab_data[index] = {"url": url, "start_time": time.time(), "total_time": 0}
        self.current_tab_index = index

    def close_tab(self, index):
        self.update_current_tab_time()

        data = self.tab_data.get(index)
        if data:
            elapsed = int(data["total_time"])
            print(f"Closed {data['url']} → {elapsed} seconds")
            update_db(self.user_id, data["url"], elapsed)

        self.tabs.removeTab(index)
        self.tab_data.pop(index, None)

        self.current_tab_index = self.tabs.currentIndex()
        if self.current_tab_index in self.tab_data:
            self.tab_data[self.current_tab_index]["start_time"] = time.time()

        self.update_total_time()

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

        # Check daily limit
        if not check_limit(self.user_id, url):
            self.statusBar().showMessage(f"Daily limit reached for {url}. Cannot open for 24h.")
            return

        current_browser = self.tabs.currentWidget()
        current_browser.setUrl(QUrl(url))

        index = self.tabs.currentIndex()
        if index in self.tab_data:
            self.tab_data[index]["url"] = url
        self.tabs.setTabText(index, url[:15])

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

        # Update DB
        update_db(self.user_id, data["url"], int(elapsed))

        self.update_total_time()

    def update_total_time(self):
        total = sum(tab["total_time"] for tab in self.tab_data.values())
        self.status.setText(f"Total Time: {int(total)} sec")

    # ---------------- ON APP CLOSE ----------------
    def closeEvent(self, event):
        self.update_current_tab_time()
        print("\nFinal Usage Report:")
        for tab in self.tab_data.values():
            print(f"{tab['url']} → {int(tab['total_time'])} seconds")
        event.accept()


# ---------------- RUN APP ----------------
app = QApplication(sys.argv)
window = MiniBrowser(user_id=1)
window.show()
sys.exit(app.exec_())
