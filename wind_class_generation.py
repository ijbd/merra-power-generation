   
                #papers talk about median giving more accurate estimations
                finalWindSpeed = np.median(finalWindSpeed100)

                #used for assinging iec levels for each year, slow way, could use np.where instead, but easier to understand
                '''
                if finalWindSpeed >= 9:
                    iecLevel = 1
                elif finalWindSpeed >= 8:
                    iecLevel = 2
                elif finalWindSpeed >= 6.5:
                    iecLevel = 3
                elif finalWindSpeed:
                    iecLevel = 0
                '''
                windSpeedArrayCul[lat][lon] += finalWindSpeed
                latLongIndex += 1

    #finding mean for each lat long wind speed value for time period of years
    windSpeedArrayCul = windSpeedArrayCul / len(yearList)

    #values not suitable for wind are assigned 0 value
    windSpeedArrayCul = np.where((windSpeedArrayCul < 6.5) & (windSpeedArrayCul >= 0), 0,windSpeedArrayCul)

    #Wind IEC level 1  anything >= 9 m/s
    windSpeedArrayCul = np.where(windSpeedArrayCul >= 9, 1,windSpeedArrayCul)

    #Wind IEC level 2 8 m/s -> 9 m/s
    windSpeedArrayCul = np.where(windSpeedArrayCul >= 8, 2,windSpeedArrayCul)

    #Wind IEC level 3 6.5 m/s -> 8 m/s
    windSpeedArrayCul = np.where(windSpeedArrayCul >= 6.5, 3,windSpeedArrayCul)

    #Wind level 4 offshore wind yet to be developed
    windSpeedArrayCul = np.where(windSpeedArrayCul < 0, 4,windSpeedArrayCul)

