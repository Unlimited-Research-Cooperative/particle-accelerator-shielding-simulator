import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFormLayout, QProgressBar,
                             QScrollArea, QSizePolicy, QHBoxLayout)
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

    def __init__(self, photon_energy, shielding_thickness, density, tvl, initial_dose_rate, em_params, ion_params, msc_params, parent=None):
        super(SimulationThread, self).__init__(parent)
        self.photon_energy = photon_energy
        self.shielding_thickness = shielding_thickness
        self.density = density
        self.tvl = tvl
        self.initial_dose_rate = initial_dose_rate
        self.em_params = em_params
        self.ion_params = ion_params
        self.msc_params = msc_params

    def run(self):
        uncertainties = []
        iterations = []
        num_events = 1000000

        for i in range(100):  # Adjust the number of iterations as needed
            total_energy_deposited = run_simulation(self.photon_energy, self.shielding_thickness, self.density)
            attenuation = calculate_attenuation(total_energy_deposited, self.photon_energy, num_events)
            dose_rate = calculate_dose_rate(total_energy_deposited, self.initial_dose_rate, self.photon_energy, num_events)

            uncertainties.append(calculate_uncertainty(i))
            iterations.append(i)

            self.update_progress.emit((i + 1) * 10 // 100)
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

        self.photonEnergyInput = QLineEdit("1.0")
        self.shieldingInput = QLineEdit("10.0")
        self.tvlInput = QLineEdit("1.0")
        self.doseRateInput = QLineEdit("1.0")
        self.densityInput = QLineEdit("2.35")

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

        self.additionalParamsButton = QPushButton('Additional Parameters')
        self.additionalParamsButton.setCheckable(True)
        self.additionalParamsButton.setChecked(False)
        self.additionalParamsButton.clicked.connect(self.toggle_additional_params)

        self.additionalParamsWidget = QWidget()
        additionalParamsLayout = QFormLayout()
        self.additionalParamsWidget.setStyleSheet("background-color: #000000;")

        # Adding inputs for Electromagnetic Physics Parameters
        self.lpmEffectInput = QLineEdit("1")
        self.useSamplingTablesInput = QLineEdit("0")
        self.applyCutsInput = QLineEdit("0")
        self.transportationWithMscInput = QLineEdit("Disabled")
        self.useGeneralProcessInput = QLineEdit("1")
        self.linearPolarisationGammaInput = QLineEdit("0")
        self.photoeffectBelowKShellInput = QLineEdit("1")
        self.quantumEntanglementInput = QLineEdit("0")
        self.xSectionFactorInput = QLineEdit("0.8")
        self.minKineticEnergyInput = QLineEdit("100")
        self.maxKineticEnergyInput = QLineEdit("100000")
        self.numBinsPerDecadeInput = QLineEdit("7")
        self.verboseLevelInput = QLineEdit("1")
        self.verboseLevelWorkerInput = QLineEdit("0")
        self.bremsstrahlungThresholdEInput = QLineEdit("100000")
        self.bremsstrahlungThresholdMuInput = QLineEdit("100000")
        self.lowestTripletEnergyInput = QLineEdit("1")
        self.linearPolarisationSamplingInput = QLineEdit("0")
        self.gammaConversionModelTypeInput = QLineEdit("0")
        self.gammaConversionModelIonInput = QLineEdit("0")
        self.livermoreDataDirectoryInput = QLineEdit("epics_2017")

        em_labels = {
            'LPM Effect Enabled (0/1):': self.lpmEffectInput,
            'Enable Sampling Tables (0/1):': self.useSamplingTablesInput,
            'Apply Cuts (0/1):': self.applyCutsInput,
            'Transportation With Msc (Disabled/Enabled):': self.transportationWithMscInput,
            'Use General Process (0/1):': self.useGeneralProcessInput,
            'Linear Polarisation Gamma (0/1):': self.linearPolarisationGammaInput,
            'Photoeffect Below K-Shell (0/1):': self.photoeffectBelowKShellInput,
            'Quantum Entanglement (0/1):': self.quantumEntanglementInput,
            'X-Section Factor (0-1):': self.xSectionFactorInput,
            'Min Kinetic Energy (eV):': self.minKineticEnergyInput,
            'Max Kinetic Energy (TeV):': self.maxKineticEnergyInput,
            'Number of Bins per Decade:': self.numBinsPerDecadeInput,
            'Verbose Level (0-3):': self.verboseLevelInput,
            'Verbose Level Worker (0-3):': self.verboseLevelWorkerInput,
            'Bremsstrahlung Threshold for e+- (TeV):': self.bremsstrahlungThresholdEInput,
            'Bremsstrahlung Threshold for Muons (TeV):': self.bremsstrahlungThresholdMuInput,
            'Lowest Triplet Energy (MeV):': self.lowestTripletEnergyInput,
            'Linear Polarisation Sampling (0/1):': self.linearPolarisationSamplingInput,
            'Gamma Conversion Model Type (0/1):': self.gammaConversionModelTypeInput,
            'Gamma Conversion Model on Ion (0/1):': self.gammaConversionModelIonInput,
            'Livermore Data Directory:': self.livermoreDataDirectoryInput,
        }

        for text, widget in em_labels.items():
            label = QLabel(text)
            label.setStyleSheet("color: #00FFFF; background-color: #000000;")
            additionalParamsLayout.addRow(label, widget)

        # Adding inputs for Ionisation Parameters
        self.stepFunctionElectronsInput = QLineEdit("(0.2, 1)")
        self.stepFunctionMuonsInput = QLineEdit("(0.2, 0.1)")
        self.stepFunctionLightIonsInput = QLineEdit("(0.2, 0.1)")
        self.stepFunctionGeneralIonsInput = QLineEdit("(0.2, 0.1)")
        self.lowestEEnergyInput = QLineEdit("1")
        self.lowestMuonEnergyInput = QLineEdit("1")
        self.useICRU90DataInput = QLineEdit("0")
        self.fluctuationsInput = QLineEdit("1")
        self.fluctuationModelInput = QLineEdit("Urban")
        self.birksSaturationInput = QLineEdit("0")
        self.buildCSDARangeInput = QLineEdit("0")
        self.useCutAsRangeInput = QLineEdit("0")
        self.angularGeneratorInterfaceInput = QLineEdit("0")
        self.maxCSDARangeInput = QLineEdit("1")
        self.maxNIELKineticEnergyInput = QLineEdit("0")
        self.linearLossLimitInput = QLineEdit("0.01")
        self.pairProductionByMuInput = QLineEdit("0")

        ion_labels = {
            'Step Function for Electrons (tuple):': self.stepFunctionElectronsInput,
            'Step Function for Muons (tuple):': self.stepFunctionMuonsInput,
            'Step Function for Light Ions (tuple):': self.stepFunctionLightIonsInput,
            'Step Function for General Ions (tuple):': self.stepFunctionGeneralIonsInput,
            'Lowest Electron Kinetic Energy (keV):': self.lowestEEnergyInput,
            'Lowest Muon Kinetic Energy (keV):': self.lowestMuonEnergyInput,
            'Use ICRU90 Data (0/1):': self.useICRU90DataInput,
            'Enable Fluctuations of dE/dx (0/1):': self.fluctuationsInput,
            'Fluctuation Model for Leptons and Hadrons:': self.fluctuationModelInput,
            'Built-in Birks Saturation (0/1):': self.birksSaturationInput,
            'Build CSDA Range (0/1):': self.buildCSDARangeInput,
            'Use Cut as Final Range (0/1):': self.useCutAsRangeInput,
            'Angular Generator Interface (0/1):': self.angularGeneratorInterfaceInput,
            'Max CSDA Range (GeV):': self.maxCSDARangeInput,
            'Max NIEL Kinetic Energy (eV):': self.maxNIELKineticEnergyInput,
            'Linear Loss Limit:': self.linearLossLimitInput,
            'Pair Production by Mu (0/1):': self.pairProductionByMuInput,
        }

        for text, widget in ion_labels.items():
            label = QLabel(text)
            label.setStyleSheet("color: #00FFFF; background-color: #000000;")
            additionalParamsLayout.addRow(label, widget)

        # Adding inputs for Multiple Scattering Parameters
        self.mscStepLimitAlgElectronsInput = QLineEdit("1")
        self.mscStepLimitAlgMuonsInput = QLineEdit("0")
        self.mscLateralDisplacementElectronsInput = QLineEdit("1")
        self.mscLateralDisplacementMuonsInput = QLineEdit("0")
        self.urbanMscModelInput = QLineEdit("1")
        self.rangeFactorElectronsInput = QLineEdit("0.04")
        self.rangeFactorMuonsInput = QLineEdit("0.2")
        self.geometryFactorElectronsInput = QLineEdit("2.5")
        self.safetyFactorElectronsInput = QLineEdit("0.6")
        self.skinParameterElectronsInput = QLineEdit("1")
        self.lambdaLimitElectronsInput = QLineEdit("1")
        self.mottCorrectionInput = QLineEdit("0")
        self.angularLimitFactorInput = QLineEdit("1")
        self.fixedAngularLimitInput = QLineEdit("3.1416")
        self.upperEnergyLimitElectronsInput = QLineEdit("100")
        self.electronSingleScatteringModelInput = QLineEdit("0")
        self.nuclearFormFactorInput = QLineEdit("1")
        self.screeningFactorInput = QLineEdit("1")

        msc_labels = {
            'Type of MSC Step Limit Algorithm for Electrons:': self.mscStepLimitAlgElectronsInput,
            'Type of MSC Step Limit Algorithm for Muons:': self.mscStepLimitAlgMuonsInput,
            'MSC Lateral Displacement for Electrons (0/1):': self.mscLateralDisplacementElectronsInput,
            'MSC Lateral Displacement for Muons (0/1):': self.mscLateralDisplacementMuonsInput,
            'Urban MSC Model Lateral Displacement (0/1):': self.urbanMscModelInput,
            'Range Factor for MSC Step Limit for Electrons:': self.rangeFactorElectronsInput,
            'Range Factor for MSC Step Limit for Muons:': self.rangeFactorMuonsInput,
            'Geometry Factor for MSC Step Limitation of Electrons:': self.geometryFactorElectronsInput,
            'Safety Factor for MSC Step Limit for Electrons:': self.safetyFactorElectronsInput,
            'Skin Parameter for MSC Step Limitation of Electrons:': self.skinParameterElectronsInput,
            'Lambda Limit for MSC Step Limit for Electrons (mm):': self.lambdaLimitElectronsInput,
            'Use Mott Correction for Electron Scattering (0/1):': self.mottCorrectionInput,
            'Angular Limit Factor for Single/Multiple Scattering:': self.angularLimitFactorInput,
            'Fixed Angular Limit for Single/Multiple Scattering (rad):': self.fixedAngularLimitInput,
            'Upper Energy Limit for Electron MSC (MeV):': self.upperEnergyLimitElectronsInput,
            'Type of Electron Single Scattering Model:': self.electronSingleScatteringModelInput,
            'Type of Nuclear Form-Factor:': self.nuclearFormFactorInput,
            'Screening Factor:': self.screeningFactorInput,
        }

        for text, widget in msc_labels.items():
            label = QLabel(text)
            label.setStyleSheet("color: #00FFFF; background-color: #000000;")
            additionalParamsLayout.addRow(label, widget)

        self.additionalParamsWidget.setLayout(additionalParamsLayout)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.additionalParamsWidget)
        self.scrollArea.setFixedHeight(300)
        self.scrollArea.setVisible(False)
        self.scrollArea.setStyleSheet("background-color: #000000;")

        self.startButton = QPushButton('Start Simulation')
        self.startButton.clicked.connect(self.run_simulation)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        
        self.resultLabel = QLabel('Results will be displayed here')
        self.resultLabel.setStyleSheet("color: #00FFFF; background-color: #000000;")

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #000000;")
        self.set_plot_style()

        layout.addLayout(formLayout)
        layout.addWidget(self.additionalParamsButton)
        layout.addWidget(self.scrollArea)
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

            em_params = {
                'lpm_effect': int(self.lpmEffectInput.text()),
                'use_sampling_tables': int(self.useSamplingTablesInput.text()),
                'apply_cuts': int(self.applyCutsInput.text()),
                'transportation_with_msc': self.transportationWithMscInput.text(),
                'use_general_process': int(self.useGeneralProcessInput.text()),
                'linear_polarisation_gamma': int(self.linearPolarisationGammaInput.text()),
                'photoeffect_below_kshell': int(self.photoeffectBelowKShellInput.text()),
                'quantum_entanglement': int(self.quantumEntanglementInput.text()),
                'x_section_factor': float(self.xSectionFactorInput.text()),
                'min_kinetic_energy': float(self.minKineticEnergyInput.text()) * eV,
                'max_kinetic_energy': float(self.maxKineticEnergyInput.text()) * TeV,
                'num_bins_per_decade': int(self.numBinsPerDecadeInput.text()),
                'verbose_level': int(self.verboseLevelInput.text()),
                'verbose_level_worker': int(self.verboseLevelWorkerInput.text()),
                'bremsstrahlung_threshold_e': float(self.bremsstrahlungThresholdEInput.text()) * TeV,
                'bremsstrahlung_threshold_mu': float(self.bremsstrahlungThresholdMuInput.text()) * TeV,
                'lowest_triplet_energy': float(self.lowestTripletEnergyInput.text()) * MeV,
                'linear_polarisation_sampling': int(self.linearPolarisationSamplingInput.text()),
                'gamma_conversion_model_type': int(self.gammaConversionModelTypeInput.text()),
                'gamma_conversion_model_ion': int(self.gammaConversionModelIonInput.text()),
                'livermore_data_directory': self.livermoreDataDirectoryInput.text(),
            }

            ion_params = {
                'step_function_electrons': tuple(map(float, self.stepFunctionElectronsInput.text().strip('()').split(','))),
                'step_function_muons': tuple(map(float, self.stepFunctionMuonsInput.text().strip('()').split(','))),
                'step_function_light_ions': tuple(map(float, self.stepFunctionLightIonsInput.text().strip('()').split(','))),
                'step_function_general_ions': tuple(map(float, self.stepFunctionGeneralIonsInput.text().strip('()').split(','))),
                'lowest_e_energy': float(self.lowestEEnergyInput.text()) * keV,
                'lowest_muon_energy': float(self.lowestMuonEnergyInput.text()) * keV,
                'use_icru90_data': int(self.useICRU90DataInput.text()),
                'fluctuations': int(self.fluctuationsInput.text()),
                'fluctuation_model': self.fluctuationModelInput.text(),
                'birks_saturation': int(self.birksSaturationInput.text()),
                'build_csda_range': int(self.buildCSDARangeInput.text()),
                'use_cut_as_range': int(self.useCutAsRangeInput.text()),
                'angular_generator_interface': int(self.angularGeneratorInterfaceInput.text()),
                'max_csda_range': float(self.maxCSDARangeInput.text()) * GeV,
                'max_niel_kinetic_energy': float(self.maxNIELKineticEnergyInput.text()) * eV,
                'linear_loss_limit': float(self.linearLossLimitInput.text()),
                'pair_production_by_mu': int(self.pairProductionByMuInput.text()),
            }

            msc_params = {
                'msc_step_limit_alg_electrons': int(self.mscStepLimitAlgElectronsInput.text()),
                'msc_step_limit_alg_muons': int(self.mscStepLimitAlgMuonsInput.text()),
                'msc_lateral_displacement_electrons': int(self.mscLateralDisplacementElectronsInput.text()),
                'msc_lateral_displacement_muons': int(self.mscLateralDisplacementMuonsInput.text()),
                'urban_msc_model': int(self.urbanMscModelInput.text()),
                'range_factor_electrons': float(self.rangeFactorElectronsInput.text()),
                'range_factor_muons': float(self.rangeFactorMuonsInput.text()),
                'geometry_factor_electrons': float(self.geometryFactorElectronsInput.text()),
                'safety_factor_electrons': float(self.safetyFactorElectronsInput.text()),
                'skin_parameter_electrons': float(self.skinParameterElectronsInput.text()),
                'lambda_limit_electrons': float(self.lambdaLimitElectronsInput.text()) * mm,
                'mott_correction': int(self.mottCorrectionInput.text()),
                'angular_limit_factor': float(self.angularLimitFactorInput.text()),
                'fixed_angular_limit': float(self.fixedAngularLimitInput.text()) * rad,
                'upper_energy_limit_electrons': float(self.upperEnergyLimitElectronsInput.text()) * MeV,
                'electron_single_scattering_model': int(self.electronSingleScatteringModelInput.text()),
                'nuclear_form_factor': int(self.nuclearFormFactorInput.text()),
                'screening_factor': float(self.screeningFactorInput.text()),
            }

            self.simulation_thread = SimulationThread(photon_energy, shielding_thickness, density, tvl, initial_dose_rate, em_params, ion_params, msc_params)
            self.simulation_thread.update_progress.connect(self.progressBar.setValue)
            self.simulation_thread.update_results.connect(self.update_results)
            self.simulation_thread.update_plot.connect(self.update_plot)
            self.simulation_thread.start()
        except ValueError:
            self.resultLabel.setText('Please enter valid numerical values.')

    def toggle_additional_params(self):
        self.scrollArea.setVisible(self.additionalParamsButton.isChecked())

    def show_visualization(self):
        run_visualization()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Geant4SimulationApp()
    ex.show()
    sys.exit(app.exec_())
