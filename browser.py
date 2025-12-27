import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLineEdit, QToolBar, QAction,
    QTabWidget, QFileDialog, QVBoxLayout, QLabel, QListWidget,
    QHBoxLayout, QPushButton, QCheckBox, QDialog, QComboBox
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEngineProfile, QWebEnginePage, QWebEngineDownloadItem
)
from PyQt5.QtCore import QUrl

# ---------------- Runtime Storage ---------------- #
history = []
bookmarks = []
password_store = {}

SETTINGS = {
    "search_engine": "Google",
    "homepage": "https://www.google.com",
    "dark_mode": True,
    "show_tabs": True,
    "show_address": True
}

SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={}",
    "Bing": "https://www.bing.com/search?q={}",
    "DuckDuckGo": "https://duckduckgo.com/?q={}"
}

# ---------- Settings Window ----------
class SettingsWindow(QDialog):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        layout = QVBoxLayout(self)

        # Search engine
        layout.addWidget(QLabel("Search Engine"))
        self.search_box = QComboBox()
        self.search_box.addItems(SEARCH_ENGINES.keys())
        self.search_box.setCurrentText(SETTINGS["search_engine"])
        self.search_box.currentTextChanged.connect(self.set_search)
        layout.addWidget(self.search_box)

        # Homepage
        layout.addWidget(QLabel("Homepage URL"))
        self.home_edit = QLineEdit(SETTINGS["homepage"])
        self.home_edit.returnPressed.connect(self.set_home)
        layout.addWidget(self.home_edit)

        # Dark mode toggle
        self.dark_toggle = QCheckBox("Dark Mode")
        self.dark_toggle.setChecked(SETTINGS["dark_mode"])
        self.dark_toggle.stateChanged.connect(browser.toggle_dark)
        layout.addWidget(self.dark_toggle)

        layout.addWidget(QPushButton("Close", clicked=self.accept))

    def set_search(self, value):
        SETTINGS["search_engine"] = value

    def set_home(self):
        SETTINGS["homepage"] = self.home_edit.text()

# ---------- Download Manager ----------
class DownloadManager(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloads")
        self.resize(500, 300)
        self.layout = QVBoxLayout(self)

    def add_download(self, path):
        self.layout.addWidget(QLabel(path))

# ---------- Browser ----------
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyChrome")
        self.resize(1500, 900)

        self.profile = QWebEngineProfile.defaultProfile()
        self.downloads = DownloadManager()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        self.tabs.currentChanged.connect(self.update_url)
        self.setCentralWidget(self.tabs)

        self.create_toolbar()
        self.add_tab()
        self.toggle_dark(SETTINGS["dark_mode"])

    # ---------- Toolbar ----------
    def create_toolbar(self):
        bar = QToolBar()
        self.addToolBar(bar)

        def btn(t, f):
            a = QAction(t, self)
            a.triggered.connect(f)
            bar.addAction(a)

        btn("←", lambda: self.current_tab().back())
        btn("→", lambda: self.current_tab().forward())
        btn("⟳", lambda: self.current_tab().reload())
        btn("🏠", self.go_home)

        self.url = QLineEdit()
        self.url.returnPressed.connect(self.navigate)
        bar.addWidget(self.url)

        btn("+", self.add_tab)
        btn("⭐", self.add_bookmark)
        btn("📜", self.show_history)
        btn("⚙", self.show_settings)
        btn("⬇", self.downloads.show)

    # ---------- Tabs ----------
    def add_tab(self):
        view = QWebEngineView()
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)
        view.setUrl(QUrl(SETTINGS["homepage"]))

        view.urlChanged.connect(lambda u: history.append(u.toString()))
        page.profile().downloadRequested.connect(self.handle_download)

        self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentWidget(view)

    def current_tab(self):
        return self.tabs.currentWidget()

    # ---------- Navigation ----------
    def navigate(self):
        text = self.url.text().strip()
        engine = SEARCH_ENGINES[SETTINGS["search_engine"]]

        if "." in text and " " not in text:
            if not text.startswith("http"):
                text = "https://" + text
            self.current_tab().setUrl(QUrl(text))
        else:
            self.current_tab().setUrl(QUrl(engine.format(text)))

    def go_home(self):
        self.current_tab().setUrl(QUrl(SETTINGS["homepage"]))

    def update_url(self):
        if self.current_tab():
            self.url.setText(self.current_tab().url().toString())

    # ---------- History / Bookmarks ----------
    def show_history(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("History")
        dlg.resize(400, 500)
        layout = QVBoxLayout(dlg)
        list_widget = QListWidget()
        list_widget.addItems(history)
        list_widget.itemClicked.connect(lambda item: self.current_tab().setUrl(QUrl(item.text())))
        layout.addWidget(list_widget)
        dlg.exec_()

    def add_bookmark(self):
        url = self.current_tab().url().toString()
        if url not in bookmarks:
            bookmarks.append(url)

    def show_settings(self):
        SettingsWindow(self).exec_()

    # ---------- Appearance ----------
    def toggle_dark(self, state):
        SETTINGS["dark_mode"] = bool(state)
        self.setStyleSheet(
            "QMainWindow{background:#1e1e1e;}QLineEdit{background:#333;color:white;}"
            if state else ""
        )

    # ---------- Downloads ----------
    def handle_download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if path:
            download.setPath(path)
            download.accept()
            self.downloads.add_download(path)

# ---------- Run ----------
app = QApplication(sys.argv)
window = Browser()
window.show()
sys.exit(app.exec_())
