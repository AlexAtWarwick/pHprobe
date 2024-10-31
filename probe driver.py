import serial
import time
import csv
from datetime import datetime
current_time = datetime.now().strftime('%Y-%m-%d %H%M%S')
filename= current_time + "_measurement_file.csv"
def cleaner(data):
    formattedData=None
    if data[0]=='pH' or data[0]=='COND':
        mode=data[0]
        value=data[1]
        units=data[2]
        temp=data[5]
        tempunits=data[6]
        formattedData={"probe mode":mode, "Value":value, "Units":units, "Temperature":temp, "Temperature units":tempunits}
    else:
        raise Exception("mode neither ph nor COND??")
    return(formattedData)

def extract_measurement(lines):
    """Extracts pH, conductivity, and their associated temperature values from response lines."""
    data=lines[2]
    dataList=data.split(',')
    #print(dataList)
    indexCH1=dataList.index('CH-1')
    indexCH2=dataList.index('CH-2')
    listCH1=dataList[indexCH1+1:indexCH2]
    listCH2=dataList[indexCH2+1:-1]
    #print("CHlist:",listCH1,print(cleaner(listCH1)))
    #print("CH2List:",listCH2,print(cleaner(listCH2)))
    CH1=cleaner(listCH1)
    CH2=cleaner(listCH2)
    return CH1,CH2
def continuous_measurement(port='COM7', interval=10, csv_file=filename):#Port is comm port, check in device manager for the usb port
    """Continuously reads pH, conductivity, and temperatures, logs them to a CSV with timestamp and relative time."""
    start_time = time.time()

    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Relative Time (s)", "pH Value", "pH Temperature (C)",
                         "Conductivity Value", "Conductivity Temperature (C)"])
        try:

            ser = serial.Serial(port, baudrate=9600, bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                timeout=1)
            print(f"Connected to {port}")
            while True:
                loop_start_time = time.time()
                ser.reset_input_buffer()
                ser.write(b'GETMEAS\r')
                time.sleep(0.5)#give time for response, and catch all responses
                lines = []
                while ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    lines.append(line)
                    time.sleep(0.1)
                try:
                    CH1,CH2 = extract_measurement(lines)#find the channels, this may not work with one channel
                    if CH1["probe mode"]== "pH":
                        ph_value=CH1["Value"]
                        ph_temp=CH1["Temperature"]
                        if CH2["probe mode"]== "COND":
                            cond_value=CH2["Value"]
                            cond_temp=CH2["Temperature"]
                    elif CH1["probe mode"]== "COND":
                        ph_value=CH1["Value"]
                        ph_temp=CH1["Temperature"]
                        if CH2["probe mode"]== "pH":
                            cond_value=CH2["Value"]
                            cond_temp=CH2["Temperature"]
                    else:
                        print("Error determining modes, fix the code :)")
                        ph_value=None
                        ph_temp=None,
                        cond_value=None
                        cond_temp=None
                    # Log data to CSV
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    relative_time = round(time.time() - start_time, 5)
                    writer.writerow([current_time, relative_time, ph_value, ph_temp, cond_value, cond_temp])
                    print(f"{current_time} | Relative Time: {relative_time}s | pH: {ph_value} | pH Temp: {ph_temp}C | "
                          f"Conductivity: {cond_value} | Cond Temp: {cond_temp}C")
                    file.flush()
                except:
                    print("Channels not found, meter in correct mode?")
                    print(lines)
                elapsed_time = time.time() - loop_start_time
                time.sleep(max(0, interval - elapsed_time))

        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            if 'ser' in locals() and ser.is_open:
                ser.close()
                print("Serial port closed.")

continuous_measurement()
