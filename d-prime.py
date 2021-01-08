from analyzeBehavioral import *


vehicleFile = ""
drugFile = ""




'''
    sheetData = []
    headings = []
    ws32 = wb.create_sheet(title='Sensitivity')
    headings.extend(["Contrast", "d' sensitivity"])
    for im in sorted(imageWiseTrueLatencies.keys(), key=getContrast):
        latencies = imageWiseTrueLatencies.get(im)
        try:
            z1 = (im.true_avg_latency - im.all_avg_latency) / im.all_SD_latency
            z2 = (TIMEOUTS.get(preset) - im.all_avg_latency) / im.all_SD_latency
            d = z2 - z1  #(TIMEOUTS.get(preset) - im.true_avg_latency) / (0.25 * im.true_SD_latency)

        except TypeError:
            d = "N/A"
        sheetData.append([getContrast(im), d])
    ws32.append(headings)
    for row in sheetData:
        try:
            ws32.append(row)
        except ValueError:
            pass'''

