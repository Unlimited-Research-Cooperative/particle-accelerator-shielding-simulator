import os
from geant4_pybind import *
from PyQt5.QtCore import QThread
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

os.environ['G4ENSDFSTATEDATA'] = '/home/vincent/geant4/data/G4ENSDFSTATE2.3'

class MySensitiveDetector(G4VSensitiveDetector):
    def __init__(self, name):
        super(MySensitiveDetector, self).__init__(name)
        self.total_energy_deposited = 0

    def ProcessHits(self, step, touchable_history):
        energy_deposited = step.GetTotalEnergyDeposit()
        self.total_energy_deposited += energy_deposited
        print(f"Energy deposited in this step: {energy_deposited} MeV")
        return True

    def GetTotalEnergyDeposited(self):
        return self.total_energy_deposited

    def Reset(self):
        self.total_energy_deposited = 0

class MyDetectorConstruction(G4VUserDetectorConstruction):
    def __init__(self, shielding_thickness=68.0, density=2.35):
        super(MyDetectorConstruction, self).__init__()
        self.shielding_thickness = shielding_thickness
        self.density = density
        self.sensitive_detector = MySensitiveDetector("ShieldSD")

    def Construct(self):
        nist = G4NistManager.Instance()

        # Use G4_CONCRETE directly
        concrete = nist.FindOrBuildMaterial("G4_CONCRETE")
        air = nist.FindOrBuildMaterial("G4_AIR")

        # World volume
        world_size = 10.0 * m
        solidWorld = G4Box("World", world_size / 2, world_size / 2, world_size / 2)
        logicWorld = G4LogicalVolume(solidWorld, air, "World")
        physWorld = G4PVPlacement(None, G4ThreeVector(), logicWorld, "World", None, False, 0)

        # Room dimensions (inner room)
        room_length = 5.0 * m
        room_width = 5.0 * m
        room_height = 3.0 * m
        shielding_thickness = self.shielding_thickness * cm

        # Outer room dimensions including wall thickness
        outer_length = room_length + 2 * shielding_thickness
        outer_width = room_width + 2 * shielding_thickness
        outer_height = room_height + 2 * shielding_thickness

        # Create the outer box
        solidOuterBox = G4Box("OuterBox", outer_length / 2, outer_width / 2, outer_height / 2)
        # Create the inner box
        solidInnerBox = G4Box("InnerBox", room_length / 2, room_width / 2, room_height / 2)

        # Subtract inner box from outer box to create walls
        solidShield = G4SubtractionSolid("Shield", solidOuterBox, solidInnerBox)
        logicShield = G4LogicalVolume(solidShield, concrete, "Shield")
        G4PVPlacement(None, G4ThreeVector(), logicShield, "Shield", logicWorld, False, 0)

        # Position the sensitive detector just outside the wall
        detector_position = G4ThreeVector((room_length / 2) + shielding_thickness + 1.0 * cm, 0, 0)
        solidDetector = G4Box("Detector", 0.1 * cm, room_width / 2, room_height / 2)
        logicDetector = G4LogicalVolume(solidDetector, air, "Detector")
        G4PVPlacement(None, detector_position, logicDetector, "Detector", logicWorld, False, 0)

        logicDetector.SetSensitiveDetector(self.sensitive_detector)

        return physWorld

    def GetSensitiveDetector(self):
        return self.sensitive_detector

class MyPrimaryGeneratorAction(G4VUserPrimaryGeneratorAction):
    def __init__(self, energy):
        super(MyPrimaryGeneratorAction, self).__init__()
        self.particleGun = G4ParticleGun(1)
        self.particleGun.SetParticleDefinition(G4Gamma.Gamma())
        self.particleGun.SetParticleEnergy(energy)
        self.particleGun.SetParticlePosition(G4ThreeVector(-2.5 * m + 1.0 * m, 0, 0))  # Start 1 meter from the wall inside the room
        self.particleGun.SetParticleMomentumDirection(G4ThreeVector(1, 0, 0))  # Aim towards the wall

    def GeneratePrimaries(self, anEvent):
        self.particleGun.GeneratePrimaryVertex(anEvent)

class MyPhysicsList(G4VModularPhysicsList):
    def __init__(self):
        super(MyPhysicsList, self).__init__()
        self.RegisterPhysics(G4EmStandardPhysics())

class MyEventAction(G4UserEventAction):
    def __init__(self, detector):
        super(MyEventAction, self).__init__()
        self.detector = detector
        self.total_energy_deposited = 0

    def BeginOfEventAction(self, event):
        self.detector.Reset()

    def EndOfEventAction(self, event):
        self.total_energy_deposited += self.detector.GetTotalEnergyDeposited()
        print(f"Total energy deposited so far: {self.total_energy_deposited} MeV")

    def GetTotalEnergyDeposited(self):
        return self.total_energy_deposited

class MyActionInitialization(G4VUserActionInitialization):
    def __init__(self, energy, detector):
        super(MyActionInitialization, self).__init__()
        self.energy = energy
        self.detector = detector

    def Build(self):
        self.SetUserAction(MyPrimaryGeneratorAction(self.energy))
        self.SetUserAction(MyEventAction(self.detector))

class G4RunManagerSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = G4RunManager()
            cls.initialize_geant4_components(cls._instance)
        return cls._instance

    @staticmethod
    def initialize_geant4_components(run_manager):
        dummy_det = MyDetectorConstruction()
        run_manager.SetUserInitialization(dummy_det)
        run_manager.SetUserInitialization(MyPhysicsList())
        run_manager.Initialize()

def run_simulation_instance(photon_energy, shielding_thickness, density):
    run_manager = G4RunManagerSingleton.get_instance()
    
    detector_construction = MyDetectorConstruction(shielding_thickness, density)
    sensitive_detector = detector_construction.GetSensitiveDetector()
    event_action = MyEventAction(sensitive_detector)
    action_initialization = MyActionInitialization(photon_energy, sensitive_detector)
    
    run_manager.SetUserInitialization(detector_construction)
    run_manager.SetUserInitialization(action_initialization)

    ui_manager = G4UImanager.GetUIpointer()
    ui_manager.ApplyCommand("/run/initialize")
    ui_manager.ApplyCommand("/run/beamOn 10000")  # Start with a smaller number of events for debugging

    total_energy_deposited = sensitive_detector.GetTotalEnergyDeposited()
    
    return total_energy_deposited

def run_simulation(photon_energy, shielding_thickness, density, progress_callback=None):
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_simulation_instance, photon_energy, shielding_thickness, density) for _ in range(10)]  # Adjust the number of processes as needed
        total_energy_deposited = 0
        for future in as_completed(futures):
            total_energy_deposited += future.result()
            if progress_callback:
                progress_callback.emit(int((futures.index(future) + 1) / len(futures) * 100))

    return total_energy_deposited

def calculate_attenuation(total_energy_deposited, initial_energy, num_events):
    return total_energy_deposited / (initial_energy * num_events)

def calculate_dose_rate(total_energy_deposited, initial_dose_rate, photon_energy, num_events):
    deposited_dose_rate = (total_energy_deposited / num_events) / photon_energy
    return initial_dose_rate * deposited_dose_rate

def calculate_uncertainty(num_events):
    return 1.0 / (num_events + 1)

def run_visualization():
    visManager = G4VisExecutive()
    visManager.Initialize()

    ui = G4UIExecutive(len(sys.argv), sys.argv)
    UImanager = G4UImanager.GetUIpointer()
    UImanager.ApplyCommand("/vis/open OGL")
    UImanager.ApplyCommand("/vis/viewer/set/viewpointThetaPhi 70 20")
    UImanager.ApplyCommand("/vis/drawVolume")
    UImanager.ApplyCommand("/vis/viewer/set/autorefresh true")
    UImanager.ApplyCommand("/vis/scene/add/trajectories smooth")
    UImanager.ApplyCommand("/vis/scene/endOfEventAction accumulate")
    UImanager.ApplyCommand("/tracking/verbose 1")
    ui.SessionStart()

if __name__ == "__main__":
    # This part will only run when the script is executed directly, not when imported as a module
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout()

    button = QPushButton("Run Simulation")
    layout.addWidget(button)

    result_label = QLabel("Simulation results will appear here")
    layout.addWidget(result_label)

    progress_bar = QProgressBar()
    layout.addWidget(progress_bar)

    window.setLayout(layout)
    window.setWindowTitle("Geant4 Simulation GUI")
    window.resize(400, 300)

    def on_run_simulation():
        photon_energy = 1.0 * MeV  # Example energy, replace with actual input
        shielding_thickness = 10.0 * cm  # Example thickness, replace with actual input
        density = 2.35  # Example density, replace with actual input
        total_energy_deposited = run_simulation(photon_energy, shielding_thickness, density)
        attenuation = calculate_attenuation(total_energy_deposited, photon_energy, 10000)
        dose_rate = calculate_dose_rate(total_energy_deposited, 1.0, photon_energy, 10000)
        result_label.setText(f"Attenuation: {attenuation}\nDose rate: {dose_rate}")

    button.clicked.connect(on_run_simulation)
    window.show()

    sys.exit(app.exec_())

