import time
import board
import busio
import adafruit_bmp280

# Initialiser le bus I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Initialiser le capteur BMP280
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

# Optionnel : configurer la pression de référence au niveau de la mer (en hPa)
bmp280.sea_level_pressure = 1013.25

while True:
    temperature = bmp280.temperature  # en °C
    pression = bmp280.pressure         # en hPa
    altitude = bmp280.altitude          # en mètres

    print(f"Température : {temperature:.2f} °C")
    print(f"Pression : {pression:.2f} hPa")
    print(f"Altitude estimée : {altitude:.2f} m")
    print("-" * 30)

    time.sleep(2)

