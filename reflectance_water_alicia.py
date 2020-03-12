# coding: utf-8

# -----------------------
# THIS SCRIPT IS BASED ON WORK BY : Luca Brüderlin

# IMPORTS
import os
import math
import numpy as np
import pandas as pd
from scipy import interpolate as intplt
from matplotlib import pyplot as plt

# Structures for data holding
sen_sam8622 = {}
sen_sam8623 = {}
sen_sam8624 = {}


# Function to parse the data
def parseData(filePath, sensorDict):
    with open(filePath) as f:
        devId = ""
        wvl = []
        sig = []
        isSpectralData = False
        next(f)
        for line in f:
            if line.startswith("[DATA]"):
                isSpectralData = True
                next(f)
                continue
            if line.startswith("[Attributes]") or line.startswith("[END] of [Attributes]"):
                continue
            if not isSpectralData:
                data = line.strip()
                data = data.split("=")
                key = data[0].strip()
                value = data[1].strip()
                try:
                    value = float(value)
                except:
                    try:
                        value = pd.to_datetime(value, format = "%Y-%m-%d %H:%M:%S")
                    except:
                        value = value
                finally:
                    value = value
                sensorDict[key] = value
            if(isSpectralData):
                if not line.startswith("[END]"):
                    data = line.strip()
                    data = data.split(" ")
                    wvl.append(float(data[0]))
                    sig.append(float(data[1]))
    sig = np.array(sig)
    wvl = np.array(wvl)
    wvl = wvl[~np.isnan(sig)]
    sig = sig[~np.isnan(sig)]
    sensorDict["Wavelength"] = wvl
    sensorDict["Signal"] = sig


# Interpoalte the intensity values of the other two sensors at the wavelength of SAM_8624
def signalInterpolation(referenceSensor, targetSensor):
    wvl = targetSensor['Wavelength']
    intens = targetSensor['Signal']
    finterps = intplt.interp1d(wvl, intens, fill_value="extrapolate")
    targetSensor['Wavelength_interp1d'] = referenceSensor['Wavelength']
    targetSensor['Signal_interp1d'] = finterps(referenceSensor['Wavelength'])

# Reflectance
def calcReflectance(referenceSensor, sensorIrradiance, sensorWaterRadiance):
    rhosky = 0.0256 + 0.00039 + 0.000034
    # Extraction of the intensity values at 750nm to determine the Rho sky needed (Based on Neukermans 2012, p. 22)
    wvl750 = 750.94233473125
    i750 = np.where(referenceSensor.get("Wavelength") == wvl750)
    inten750_22 = sensorIrradiance.get("Signal_interp1d")[i750]
    inten750_23 = sensorWaterRadiance.get("Signal_interp1d")[i750]
    # Calculation of the above-water marine reflectance (Based on Neukermans 2012, p. 22)
    if (inten750_23/inten750_22 < 0.05):
        rhow = math.pi * ( referenceSensor.get("Signal") - (rhosky * sensorWaterRadiance.get("Signal_interp1d"))) / (sensorIrradiance.get("Signal_interp1d"))
    elif (inten750_23/inten750_22 >= 0.05):
        rhow = math.pi * (referenceSensor.get("Signal") - (0.0256 * sensorWaterRadiance.get("Signal_interp1d"))) / (sensorIrradiance.get("Signal_interp1d"))
    return rhow

# TEST
# FILES
fPath = "data/SAM_8622_calibrated.dat"
parseData(fPath, sen_sam8622)
fPath = "data/SAM_8623_calibrated.dat"
parseData(fPath, sen_sam8623)
fPath = "data/SAM_8624_calibrated.dat"
parseData(fPath, sen_sam8624)
# INTERPOLATION
signalInterpolation(sen_sam8624, sen_sam8622)
signalInterpolation(sen_sam8624, sen_sam8623)
# REFLECTANCE
rhow = calcReflectance(sen_sam8624, sen_sam8622, sen_sam8623)
