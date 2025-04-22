import sys
import json
import os
import time
import threading
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
                            QTableWidget, QTableWidgetItem, QComboBox, QFileDialog,
                            QMessageBox, QProgressBar, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

class CrawlerThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    data_ready = pyqtSignal(list)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True

    def run(self):
        try:
            self.log.emit("🚀 爬虫启动...")
            self.crawl()
        except Exception as e:
            self.error.emit(f"致命错误: {str(e)}")

    def crawl(self):
        headers = self.get_random_headers()
        visited = set()
        to_visit = [self.config['start_url']]

        while to_visit and self.running:
            url = to_visit.pop(0)
            if url in visited:
                continue

            try:
                self.log.emit(f"⌛ 正在抓取: {url}")
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.config['timeout'],
                    proxies=self.config['use_proxy'] and self.get_proxy() or None
                )

                if response.status_code == 200:
                    visited.add(url)
                    soup = BeautifulSoup(response.text, 'lxml')
                    
                    # 数据提取
                    data = {
                        'url': url,
                        'title': self.extract_title(soup),
                        'content': self.extract_content(soup),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.data_ready.emit([data])

                    # 链接发现
                    links = self.extract_links(soup, url)
                    to_visit.extend(links)
                    
                else:
                    self.log.emit(f"❌ 状态码: {response.status_code}")
            except Exception as e:
                self.log.emit(f"‼️ 抓取失败: {str(e)}")
            
            self.progress.emit(100 * len(visited) // len(to_visit))

    def get_random_headers(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        return {
            "User-Agent": random.choice(user_agents),
            "Accept-Language": "en-US,en;q=0.9"
        }

    def extract_title(self, soup):
        return soup.title.string.strip() if soup.title else "无标题"

    def extract_content(self, soup):
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return "\n".join(text.splitlines()[:500])  # 限制内容长度

    def extract_links(self, soup, base_url):
        links = set()
        for a in soup.find_all('a', href=True):
            link = urljoin(base_url, a['href'])
            if link not in visited:
                links.add(link)
        return list(links)

    def get_proxy(self):
        proxies = [
            {"http": "http://proxy1:8080", "https": "http://proxy1:8080"},
            {"http": "http://proxy2:8080", "https": "http://proxy2:8080"}
        ]
        return random.choice(proxies)

class CrawlerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.crawler = None
        self.results = []

    def initUI(self):
        self.setWindowTitle("智能网络爬虫")
        self.setGeometry(100, 100, 1000, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 配置区域
        self.config_group = QGroupBox("爬虫配置")
        config_layout = QFormLayout()
        
        self.url_input = QLineEdit("https://example.com")
        self.threads_input = QComboBox()
        self.threads_input.addItems([str(i) for i in range(1, 11)])
        self.timeout_input = QComboBox()
        self.timeout_input.addItems([str(i) for i in [5, 10, 20, 30]])
        self.proxy_check = QCheckBox("使用代理池")
        
        config_layout.addRow("起始URL:", self.url_input)
        config_layout.addRow("并发线程:", self.threads_input)
        config_layout.addRow("超时设置:", self.timeout_input)
        config_layout.addRow("", self.proxy_check)
        
        self.config_group.setLayout(config_layout)
        
        # 控制区域
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始爬取")
        self.stop_btn = QPushButton("停止")
        self.export_btn = QPushButton("导出数据")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.export_btn)
        
        # 日志区域
        self.log_group = QGroupBox("实时日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        self.progress = QProgressBar()
        log_layout.addWidget(self.progress)
        
        self.log_group.setLayout(log_layout)
        
        # 结果区域
        self.result_group = QGroupBox("抓取结果")
        result_layout = QVBoxLayout()
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["URL", "标题", "内容"])
        result_layout.addWidget(self.result_table)
        
        self.result_group.setLayout(result_layout)
        
        # 组合布局
        layout.addWidget(self.config_group, 0)
        layout.addLayout(control_layout, 0)
        layout.addWidget(self.log_group, 1)
        layout.addWidget(self.result_group, 2)

        # 信号连接
        self.start_btn.clicked.connect(self.start_crawling)
        self.stop_btn.clicked.connect(self.stop_crawling)
        self.export_btn.clicked.connect(self.export_data)

    def start_crawling(self):
        config = {
            'start_url': self.url_input.text(),
            'threads': int(self.threads_input.currentText()),
            'timeout': int(self.timeout_input.currentText()),
            'use_proxy': self.proxy_check.isChecked()
        }
        
        self.crawler = CrawlerThread(config)
        self.crawler.progress.connect(self.update_progress)
        self.crawler.log.connect(self.append_log)
        self.crawler.data_ready.connect(self.update_results)
        self.crawler.finished.connect(self.crawl_finished)
        self.crawler.error.connect(self.show_error)
        self.crawler.start()

    def stop_crawling(self):
        if self.crawler:
            self.crawler.running = False
            self.crawler.terminate()

    def update_progress(self, value):
        self.progress.setValue(value)

    def append_log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.maximum())

    def update_results(self, data):
        self.result_table.setRowCount(len(self.results) + len(data))
        for item in data:
            row = len(self.results)
            self.result_table.setItem(row, 0, QTableWidgetItem(item['url']))
            self.result_table.setItem(row, 1, QTableWidgetItem(item['title'][:50] + "..."))
            self.result_table.setItem(row, 2, QTableWidgetItem(item['content'][:100] + "..."))
        self.results.extend(data)

    def crawl_finished(self):
        self.append_log("✅ 爬取完成！共抓取 {} 条数据".format(len(self.results)))

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存数据", "", "CSV Files (*.csv);;JSON Files (*.json)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            self.append_log(f"📥 数据已导出至 {path}")

    def show_error(self, message):
        QMessageBox.critical(self, "错误", message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CrawlerApp()
    window.show()
    sys.exit(app.exec_())
