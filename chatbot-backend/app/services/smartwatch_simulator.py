"""Smartwatch data simulator for testing."""
import random
from app.models.schemas import DadosFisiologicos


class SmartWatchSimulator:
    """Simulate smartwatch physiological data."""
    
    @staticmethod
    def generate_data() -> DadosFisiologicos:
        """Generate random but realistic physiological data."""
        # Generate realistic values with some variation
        return DadosFisiologicos(
            frequencia_cardiaca=random.randint(60, 100),  # Normal range: 60-100 BPM
            saturacao_oxigenio=random.randint(95, 100),   # Normal range: 95-100%
            pressao_arterial_sistolica=random.randint(110, 130),  # Normal range: 110-130 mmHg
            pressao_arterial_diastolica=random.randint(70, 85),   # Normal range: 70-85 mmHg
            temperatura_corporal=round(random.uniform(36.1, 37.2), 1)  # Normal range: 36.1-37.2°C
        )


# HARDWARE_INTEGRATION: SmartWatchSimulator.generate_data() above takes no
# arguments because it never talks to a device. Once real hardware is
# available, it should be replaced by a function shaped like the one below,
# reached through one of two integration paths depending on where the read
# happens: the Web Bluetooth API (`navigator.bluetooth.requestDevice`)
# connecting directly to the wearable's GATT services (Heart Rate, Health
# Thermometer, Blood Pressure) from the attendant's browser, or Google Health
# Connect (Android) / Apple HealthKit (iOS) aggregating the paired device's
# samples through a native attendant app.
def read_physiological_data(smartwatch_id: str) -> DadosFisiologicos:
    """Read the latest physiological sample from a paired wearable device.

    Args:
        smartwatch_id: Identifier of the wearable/device pairing record,
            used to resolve which BLE device or Health Connect/HealthKit
            data source to read from for the patient currently being
            attended.

    Returns:
        DadosFisiologicos populated with the most recent heart rate, SpO2,
        blood pressure and body temperature samples reported by the device,
        instead of a randomly generated distribution.
    """
    raise NotImplementedError(
        "Real hardware integration is not implemented yet; "
        "use SmartWatchSimulator.generate_data() for the mocked flow."
    )


# Global smartwatch simulator instance
smartwatch_simulator = SmartWatchSimulator()
