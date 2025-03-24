import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import time
import paho.mqtt.client as mqtt
import logging
import logging.config
import os

# Initialize ADC
ADC.setup()

# MQTT Configuration
MQTT_BROKER = "raspberrypi"
MQTT_PORT = 1883
MQTT_TOPIC = "beaglebone/pins"

# Logging Setup
# Load logging config from external file
config_file = os.path.join(os.path.dirname(__file__), "logging.conf")
if os.path.exists(config_file):
    logging.config.fileConfig(config_file)
else:
    logging.basicConfig(filename='/home/debian/logs/beaglepins2mqtt.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logging.info("Starting Beaglebone PIN MQTT Bridge")

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# List of ALL GPIO pins to monitor (P8 and P9 headers)
gpio_pins = [
    "P8_3", "P8_4", "P8_5", "P8_6", "P8_7", "P8_8", "P8_9", "P8_10",
    "P8_11", "P8_12", "P8_13", "P8_14", "P8_15", "P8_16", "P8_17", "P8_18",
    "P8_19", "P8_20", "P8_21", "P8_22", "P8_23", "P8_24", "P8_25", "P8_26",
    "P9_11", "P9_12", "P9_13", "P9_14", "P9_15", "P9_16", "P9_17", "P9_18",
    "P9_19", "P9_20", "P9_21", "P9_22", "P9_23", "P9_25",
    "P9_27", "P9_28", "P9_29", "P9_30", "P9_31", "P9_41", "P9_42"
]

# List of ADC pins to monitor
adc_pins = [
    "P9_33", "P9_35", "P9_36", "P9_37", "P9_38", "P9_39", "P9_40"
]

# List of SPI pins to check for activity
spi_pins = [
    "/dev/spidev0.0", "/dev/spidev0.1", "/dev/spidev1.0", "/dev/spidev1.1"
]

# Set up GPIOs as input
for pin in gpio_pins:
    try:
        GPIO.setup(pin, GPIO.IN)
    except Exception as e:
        logging.exception(f"Failed to configure {pin}: {e}")

logging.info("Monitoring all GPIO, ADC, and SPI pins")

try:
    while True:
        pin_data = {}

        # Read GPIO values
        for pin in gpio_pins:
            try:
                pin_data[pin] = GPIO.input(pin)
            except RuntimeError:
                pin_data[pin] = "ERROR"

        # Read ADC values
        for pin in adc_pins:
            try:
                raw_value = ADC.read(pin) * 1.8  # Convert to voltage
                pin_data[pin] = round(raw_value, 3)
            except RuntimeError:
                pin_data[pin] = "ERROR"

        # Check SPI devices
        for spi in spi_pins:
            try:
                with open(spi, "rb") as f:
                    pin_data[spi] = "Active"
            except IOError:
                pin_data[spi] = "Inactive"

        # Publish data to MQTT
        client.publish(MQTT_TOPIC, str(pin_data))
        logging.info(pin_data)

        time.sleep(30)  # Adjust for desired frequency

except KeyboardInterrupt:
    logging.info("\n Monitoring stopped. Exiting...")
    GPIO.cleanup()
