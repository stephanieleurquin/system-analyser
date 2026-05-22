import sys
import psutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QTimer


def get_danger_score(name, cpu, ram):
    score = 0

    if cpu > 50:
        score += 40
    elif cpu > 20:
        score += 20

    if ram > 10:
        score += 30

    bad_keywords = ["temp", "tmp", "unknown", "virus", "hack"]
    if name and any(k in name.lower() for k in bad_keywords):
        score += 50

    return min(score, 100)


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Analyseur Système Pro")
        self.setGeometry(200, 200, 1000, 700)

        self.cpu_history = []

        self.initUI()

        psutil.cpu_percent(interval=None)
        for p in psutil.process_iter():
            p.cpu_percent(interval=None)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)

    def initUI(self):
        layout = QVBoxLayout()

        self.cpu_label = QLabel("CPU : ")
        self.ram_label = QLabel("RAM : ")
        self.disk_label = QLabel("DISK : ")

        self.refresh_btn = QPushButton("Actualiser")
        self.refresh_btn.clicked.connect(self.update_stats)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PID", "Nom", "CPU %", "Danger"])

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.disk_label)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.canvas)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_stats()

    def update_stats(self):
        # DISK
        disk = psutil.disk_usage('/')
        self.disk_label.setText(
            f"DISK : {disk.percent}% "
            f"({disk.used // (1024 ** 3)} Go / {disk.total // (1024 ** 3)} Go)"
        )

        # CPU / RAM
        cpu_total = psutil.cpu_percent()
        ram_total = psutil.virtual_memory().percent

        self.cpu_label.setText(f"CPU : {cpu_total}%")
        self.ram_label.setText(f"RAM : {ram_total}%")

        # GRAPH
        self.cpu_history.append(cpu_total)
        if len(self.cpu_history) > 30:
            self.cpu_history.pop(0)

        self.ax.clear()
        self.ax.plot(self.cpu_history)
        self.ax.set_title("CPU en temps réel")
        self.ax.set_ylim(0, 100)
        self.canvas.draw()

        # PROCESSES
        processes = []

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                cpu = proc.cpu_percent(interval=None)
                ram = proc.memory_percent()
                name = proc.info['name']

                danger = get_danger_score(name, cpu, ram)

                processes.append({
                    "pid": proc.info['pid'],
                    "name": name,
                    "cpu": cpu,
                    "danger": danger
                })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        self.table.setRowCount(len(processes))

        for row, p in enumerate(processes):
            self.table.setItem(row, 0, QTableWidgetItem(str(p["pid"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(p["name"])))
            self.table.setItem(row, 2, QTableWidgetItem(f"{p['cpu']:.1f}"))
            self.table.setItem(row, 3, QTableWidgetItem(str(p["danger"])))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
