import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFormLayout, QProgressBar, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor
from geant4_pybind import *
from geant4_simulation import run_simulation, calculate_dose_rate, calculate_uncertainty, calculate_attenuation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import time

class SimulationThread(QThread):
    update_progress = pyqtSignal(int)
    update_results = pyqtSignal(float, float)  # Attenuation, dose rate
    update_plot = pyqtSignal(list, list)  # Iterations, uncertainties

    def __init__(self, photon_energy, shielding_thickness, density, tvl, initial_dose_rate, parent=None):
        super(SimulationThread, self).__init__(parent)
        self.photon_energy = photon_energy
        self.shielding_thickness = shielding_thickness
        self.density = density
        self.tvl = tvl
        self.initial_dose_rate = initial_dose_rate

    def run(self):
        uncertainties = []
        iterations = []
        num_events = 10000

        for i in range(50000):  # Adjust the number of iterations as needed
            total_energy_deposited = run_simulation(self.photon_energy, self.shielding_thickness, self.density)
            attenuation = calculate_attenuation(total_energy_deposited, self.photon_energy, num_events)
            dose_rate = calculate_dose_rate(total_energy_deposited, self.initial_dose_rate, self.photon_energy, num_events)

            uncertainties.append(calculate_uncertainty(i))
            iterations.append(i)

            self.update_progress.emit((i + 1) * 10 // 50000)
            self.update_results.emit(attenuation, dose_rate)
            self.update_plot.emit(iterations, uncertainties)
            time.sleep(0.1)

class Geant4SimulationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Synthetic Intelligence Labs Geant4 Control Interface')
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Window)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(Qt.black))
        self.setPalette(palette)

        self.setStyleSheet("""
            QLabel {
                color: #00FFFF;
                background-color: #000000;
            }
            QLineEdit {
                color: #00FFFF;
                background-color: #000000;
                border: 1px solid #00FFFF;
            }
            QPushButton {
                color: #00FFFF;
                background-color: #000000;
                border: 1px solid #00FFFF;
            }
            QProgressBar {
                color: #00FFFF;
                background-color: #000000;
                border: 1px solid #00FFFF;
                text-align: center;
            }
        """)

        self.resize(800, 800)

        layout = QVBoxLayout()
        formLayout = QFormLayout()

        self.photonEnergyInput = QLineEdit()
        self.shieldingInput = QLineEdit()
        self.tvlInput = QLineEdit()
        self.doseRateInput = QLineEdit()
        self.densityInput = QLineEdit()

        labels = {
            'Photon Radiation (MeV):': self.photonEnergyInput,
            'Shielding Thickness (cm):': self.shieldingInput,
            'TVL (cm):': self.tvlInput,
            'Dose Rate (cGy/min):': self.doseRateInput,
            'Concrete Density (g/cm^3):': self.densityInput,
        }

        for text, widget in labels.items():
            label = QLabel(text)
            label.setStyleSheet("color: #00FFFF; background-color: #000000;")
            formLayout.addRow(label, widget)
        
        self.startButton = QPushButton('Start Simulation')
        self.startButton.clicked.connect(self.run_simulation)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        
        self.resultLabel = QLabel('Results will be displayed here')
        self.resultLabel.setStyleSheet("color: #00FFFF; background-color: #000000;")

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        layout.addLayout(formLayout)
        layout.addWidget(self.startButton)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.resultLabel)

        plotLayout = QVBoxLayout()
        plotLayout.addWidget(self.canvas)

        self.vizButton = QPushButton('Show Visualization')
        self.vizButton.clicked.connect(self.show_visualization)
        plotLayout.addWidget(self.vizButton)

        layout.addLayout(plotLayout)
        
        self.setLayout(layout)

    def set_plot_style(self):
        self.ax.set_facecolor('black')
        self.figure.patch.set_facecolor('black')
        self.ax.tick_params(axis='x', colors='#00FFFF')
        self.ax.tick_params(axis='y', colors='#00FFFF')
        self.ax.xaxis.label.set_color('#00FFFF')
        self.ax.yaxis.label.set_color('#00FFFF')
        self.ax.title.set_color('#00FFFF')
        self.ax.spines['bottom'].set_color('#00FFFF')
        self.ax.spines['top'].set_color('#00FFFF')
        self.ax.spines['left'].set_color('#00FFFF')
        self.ax.spines['right'].set_color('#00FFFF')

    def update_plot(self, iterations, uncertainties):
        self.ax.clear()
        self.ax.plot(iterations, uncertainties, marker='o', color='#00FFFF')
        self.ax.set_title('Convergence Plot')
        self.ax.set_xlabel('Iterations')
        self.ax.set_ylabel('Uncertainty')
        self.set_plot_style()
        self.canvas.draw()

    def update_results(self, attenuation, dose_rate):
        self.resultLabel.setText(f"Simulation completed!\nAttenuation: {attenuation:.6f}\nDose rate: {dose_rate:.2f} cGy/min")

    def run_simulation(self):
        try:
            photon_energy = float(self.photonEnergyInput.text()) * MeV
            shielding_thickness = float(self.shieldingInput.text()) * cm
            tvl = float(self.tvlInput.text())
            initial_dose_rate = float(self.doseRateInput.text())
            density = float(self.densityInput.text())

            self.simulation_thread = SimulationThread(photon_energy, shielding_thickness, density, tvl, initial_dose_rate)
            self.simulation_thread.update_progress.connect(self.progressBar.setValue)
            self.simulation_thread.update_results.connect(self.update_results)
            self.simulation_thread.update_plot.connect(self.update_plot)
            self.simulation_thread.start()
        except ValueError:
            self.resultLabel.setText('Please enter valid numerical values.')

    def show_visualization(self):
        run_visualization()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Geant4SimulationApp()
    ex.show()
    sys.exit(app.exec_())
