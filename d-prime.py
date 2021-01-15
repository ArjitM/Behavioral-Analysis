from analyzeBehavioral import *

"""
Bin size for latency frequency distributions.
"""
LATENCYSTEP = 0.25


vehicleFile = "/Users/arjitmisra/Documents/Kramer_Lab/Behavioral-Analysis/Dprime/RD10-N-2 Raw Data.txt"
drugFile = "/Users/arjitmisra/Documents/Kramer_Lab/Behavioral-Analysis/Dprime/RD10-T-3 Raw Data.txt"

_, _, presetV = analyze([vehicleFile], False)
imageWiseAllLatenciesV, _, imageWiseAllLatencies_1stV, _ = pokeLatencies(presetV, None)

_, _, presetD = analyze([drugFile], False)
imageWiseAllLatenciesD, _, imageWiseAllLatencies_1stD, _ = pokeLatencies(presetD, None)

if set(imageWiseAllLatenciesV) != set(imageWiseAllLatenciesD) or \
        set(imageWiseAllLatencies_1stD) != set(imageWiseAllLatencies_1stV):
    raise ValueError("Please ensure vehicle and drug experimental image sets are the same. "
                     "\nVehicle file: {0}\nDrug file:{1}".format(vehicleFile, drugFile))

wb = Workbook()
sheetData = []
headings = []
ws = wb.active
ws.title = 'Sensitivity'

for im in sorted(imageWiseAllLatenciesD.keys(), key=getContrast):
    headings.extend(["Contrast", "Bin", "Vehicle Count", "Drug Count", ""])
    latenciesD = imageWiseAllLatenciesD.get(im)
    latenciesV = imageWiseAllLatenciesV.get(im)
    contrast = getContrast(im)

    dPrime = np.abs(np.mean(latenciesD) - np.mean(latenciesV)) / np.sqrt(np.var(latenciesD) + np.var(latenciesV))

    countD, hbinD = np.histogram(latenciesD, bins=np.arange(0, TIMEOUTS.get(presetD, 10) + LATENCYSTEP, LATENCYSTEP))
    countD = list(countD)
    hbinD = list(hbinD)

    countV, hbinV = np.histogram(latenciesV, bins=np.arange(0, TIMEOUTS.get(presetV, 10) + LATENCYSTEP, LATENCYSTEP))
    countV = list(countV)
    hbinV = list(hbinV)

    hbin = hbinD if len(hbinD) > len(hbinV) else hbinV
    sheetData.append([getContrast(im)] * len(hbin))
    sheetData.append(hbin + ["", "Total", "D '"])
    sheetData.append(countD + ["", "", sum(countD), dPrime])
    sheetData.append(countV + ["", "", sum(countV)])
    sheetData.append([])

ws.append(headings)
for row in zip_longest(*sheetData, fillvalue=""):
    try:
        ws.append(row)
    except ValueError:
        pass

wb.save('/Users/arjitmisra/Documents/Kramer_Lab/Behavioral-Analysis/Dprime/dprimetry.xlsx')


