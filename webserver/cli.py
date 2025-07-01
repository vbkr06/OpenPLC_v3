import sqlite3
from sqlite3 import Error
import os
import subprocess
import openplc
#import monitoring as monitor
import time
import argparse
import random

openplc_runtime = openplc.runtime()



def configure_runtime():
    global openplc_runtime
    database = "openplc.db"
    conn = create_connection(database)
    if (conn != None):
        try:
            print("Openning database")
            cur = conn.cursor()
            cur.execute("SELECT * FROM Settings")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for row in rows:
                if (row[0] == "Modbus_port"):
                    if (row[1] != "disabled"):
                        print("Enabling Modbus on port " + str(int(row[1])))
                        openplc_runtime.start_modbus(int(row[1]))
                    else:
                        print("Disabling Modbus")
                        openplc_runtime.stop_modbus()
                elif (row[0] == "Dnp3_port"):
                    if (row[1] != "disabled"):
                        print("Enabling DNP3 on port " + str(int(row[1])))
                        openplc_runtime.start_dnp3(int(row[1]))
                    else:
                        print("Disabling DNP3")
                        openplc_runtime.stop_dnp3()
                elif (row[0] == "Enip_port"):
                    if (row[1] != "disabled"):
                        print("Enabling EtherNet/IP on port " + str(int(row[1])))
                        openplc_runtime.start_enip(int(row[1]))
                    else:
                        print("Disabling EtherNet/IP")
                        openplc_runtime.stop_enip()
                elif (row[0] == "snap7"):
                    if (row[1] != "false"):
                        print("Enabling S7 Protocol")
                        openplc_runtime.start_snap7()
                    else:
                        print("Disabling S7 Protocol")
                        openplc_runtime.stop_snap7()
                elif (row[0] == "Pstorage_polling"):
                    if (row[1] != "disabled"):
                        print("Enabling Persistent Storage with polling rate of " + str(int(row[1])) + " seconds")
                        openplc_runtime.start_pstorage(int(row[1]))
                    else:
                        print("Disabling Persistent Storage")
                        openplc_runtime.stop_pstorage()
                        delete_persistent_file()
        except Error as e:
            print("error connecting to the database" + str(e))
    else:
        print("Error opening DB")

def generate_mbconfig():
    database = "openplc.db"
    conn = create_connection(database)
    if (conn != None):
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Slave_dev")
            row = cur.fetchone()
            num_devices = int(row[0])
            mbconfig = 'Num_Devices = "' + str(num_devices) + '"'
            cur.close()
            
            cur=conn.cursor()
            cur.execute("SELECT * FROM Settings")
            rows = cur.fetchall()
            cur.close()
                    
            for row in rows:
                if (row[0] == "Slave_polling"):
                    slave_polling = str(row[1])
                elif (row[0] == "Slave_timeout"):
                    slave_timeout = str(row[1])
                    
            mbconfig += '\nPolling_Period = "' + slave_polling + '"'
            mbconfig += '\nTimeout = "' + slave_timeout + '"'
            
            cur = conn.cursor()
            cur.execute("SELECT * FROM Slave_dev")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            device_counter = 0
            for row in rows:
                mbconfig += """
# ------------
#   DEVICE """
                mbconfig += str(device_counter)
                mbconfig += """
# ------------
"""
                mbconfig += 'device' + str(device_counter) + '.name = "' + str(row[1]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.slave_id = "' + str(row[3]) + '"\n'
                if (str(row[2]) == 'ESP32' or str(row[2]) == 'ESP8266' or str(row[2]) == 'TCP'):
                    mbconfig += 'device' + str(device_counter) + '.protocol = "TCP"\n'
                    mbconfig += 'device' + str(device_counter) + '.address = "' + str(row[9]) + '"\n'
                else:
                    mbconfig += 'device' + str(device_counter) + '.protocol = "RTU"\n'
                    if (str(row[4]).startswith("COM")):
                        port_name = "/dev/ttyS" + str(int(str(row[4]).split("COM")[1]) - 1)
                    else:
                        port_name = str(row[4])
                    mbconfig += 'device' + str(device_counter) + '.address = "' + port_name + '"\n'
                mbconfig += 'device' + str(device_counter) + '.IP_Port = "' + str(row[10]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.RTU_Baud_Rate = "' + str(row[5]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.RTU_Parity = "' + str(row[6]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.RTU_Data_Bits = "' + str(row[7]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.RTU_Stop_Bits = "' + str(row[8]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.RTU_TX_Pause = "' + str(row[21]) + '"\n\n'
                
                mbconfig += 'device' + str(device_counter) + '.Discrete_Inputs_Start = "' + str(row[11]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Discrete_Inputs_Size = "' + str(row[12]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Coils_Start = "' + str(row[13]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Coils_Size = "' + str(row[14]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Input_Registers_Start = "' + str(row[15]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Input_Registers_Size = "' + str(row[16]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Holding_Registers_Read_Start = "' + str(row[17]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Holding_Registers_Read_Size = "' + str(row[18]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Holding_Registers_Start = "' + str(row[19]) + '"\n'
                mbconfig += 'device' + str(device_counter) + '.Holding_Registers_Size = "' + str(row[20]) + '"\n'
                device_counter += 1
                
            with open('./mbconfig.cfg', 'w+') as f: f.write(mbconfig)
            
        except Error as e:
            print("error connecting to the database" + str(e))
    else:
        print("Error opening DB")
  

#----------------------------------------------------------------------------
#Creates a connection with the SQLite database.
#----------------------------------------------------------------------------
""" Create a connection to the database file """
def create_connection(db_file):
   try:
      conn = sqlite3.connect(db_file)
      return conn
   except Error as e:
      print(e)

   return None

def start_plc():
    global openplc_runtime
    
    #monitor.stop_monitor()
    openplc_runtime.start_runtime()
    time.sleep(1)
    #monitor.cleanup()
    #monitor.parse_st(openplc_runtime.project_file)


def stop_plc():
    global openplc_runtime
    
    openplc_runtime.stop_runtime()
    time.sleep(1)
    #monitor.stop_monitor()


def runtime_logs():
    global openplc_runtime
    
    return openplc_runtime.logs()

def delete_persistent_file():
    if (os.path.isfile("persistent.file")):
        os.remove("persistent.file")
    print("persistent.file removed!")

def upload_program():
    
    filename = str(random.randint(1,1000000)) + ".st"
    #prog_file.save(os.path.join('st_files', filename))
        
def compile_program(st_file):
    global openplc_runtime
    
    delete_persistent_file()
    openplc_runtime.compile_program(st_file)
    
    return None
    
def compilation_logs():
    return openplc_runtime.compilation_status()

def set_program(prog_id, st_file):
    if (openplc_runtime.status() == "Compiling"): 
        pass
    database = "openplc.db"
    conn = create_connection(database)
    if (conn != None):
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Programs WHERE File=?", (st_file,))
            row = cur.fetchone()
            openplc_runtime.project_name = str(row[1])
            openplc_runtime.project_description = str(row[2])
            openplc_runtime.project_file = str(row[3])
            cur.close()
            conn.close()
        except Error as e:
            print("error connecting to the database" + str(e))
    else:
        print("error connecting to the database")
    
    delete_persistent_file()
    openplc_runtime.compile_program(st_file)
    

def remove_program(prog_id):
    if (openplc_runtime.status() == "Compiling"): 
        pass
    database = "openplc.db"
    conn = create_connection(database)
    if (conn != None):
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM Programs WHERE Prog_ID = ?", (int(prog_id),))
            conn.commit()
            cur.close()
            conn.close()
            
        except Error as e:
            print("error connecting to the database" + str(e))
            return 'Error connecting to the database. Make sure that your openplc.db file is not corrupt.<br><br>Error: ' + str(e)
    else:
        return 'Error connecting to the database. Make sure that your openplc.db file is not corrupt.'

def add_device():
    devname = ""
    devtype = ""
    devid = 1
    devip = ""
    devport = 502
    devcport = 0
    devbaud = 0
    devparity = 0
    devdata = 0
    devstop = 0
    devpause = 0
    
    di_start = 0
    di_size = 0
    do_start = 0
    do_size = 0
    ai_start = 0
    ai_size = 0
    aor_start = 0
    aor_size = 0
    aow_start = 0
    aow_size = 0
    
    (devname, devtype, devid, devcport, devbaud, devparity, devdata, devstop, devpause, devip, devport, di_start, di_size, do_start, do_size, ai_start, ai_size, aor_start, aor_size, aow_start, aow_size) \
        = sanitize_input(devname, devtype, devid, devcport, devbaud, devparity, devdata, devstop, devpause, devip, devport, di_start, di_size, do_start, do_size, ai_start, ai_size, aor_start, aor_size, aow_start, aow_size)

    database = "openplc.db"
    conn = create_connection(database)
    if (conn != None):
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO Slave_dev (dev_name, dev_type, slave_id, com_port, baud_rate, parity, data_bits, stop_bits, ip_address, ip_port, di_start, di_size, coil_start, coil_size, ir_start, ir_size, hr_read_start, hr_read_size, hr_write_start, hr_write_size, pause) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (devname, devtype, devid, devcport, devbaud, devparity, devdata, devstop, devip, devport, di_start, di_size, do_start, do_size, ai_start, ai_size, aor_start, aor_size, aow_start, aow_size, devpause))
            conn.commit()
            cur.close()
            conn.close()
            
            generate_mbconfig()
            
        except Error as e:
            print("error connecting to the database" + str(e))
            return 'Error connecting to the database. Make sure that your openplc.db file is not corrupt.<br><br>Error: ' + str(e)
    else:
        return 'Error connecting to the database. Make sure that your openplc.db file is not corrupt.'


def delete_device():
    if (openplc_runtime.status() == "Compiling"): 
        pass
    
    devid_db = 0
    database = "openplc.db"
    conn = create_connection(database)
    if (conn != None):
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM Slave_dev WHERE dev_id = ?", (int(devid_db),))
            conn.commit()
            cur.close()
            conn.close()
            generate_mbconfig()

        except Error as e:
            print("error connecting to the database" + str(e))
            return 'Error connecting to the database. Make sure that your openplc.db file is not corrupt.<br><br>Error: ' + str(e)
    else:
        return 'Error connecting to the database. Make sure that your openplc.db file is not corrupt.'


def modbus():
    #monitor.stop_monitor()
    if (openplc_runtime.status() == "Compiling"): 
        pass
    
    database = "openplc.db"
    conn = create_connection(database)
    if (conn != None):
        try:
            cur = conn.cursor()
            cur.execute("SELECT dev_id, dev_name, dev_type, di_size, coil_size, ir_size, hr_read_size, hr_write_size FROM Slave_dev")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            counter_di = 0
            counter_do = 0
            counter_ai = 0
            counter_ao = 0
            
            for row in rows:
                
                #calculate di
                if (row[3] == 0):
                    di = "-"
                else:
                    di = "%IX" + str(100 + (counter_di // 8)) + "." + str(counter_di%8) + " to "
                    counter_di += row[3];
                    di += "%IX" + str(100 + ((counter_di-1) // 8)) + "." + str((counter_di-1)%8)
                    
                #calculate do
                if (row[4] == 0):
                    do = "-"
                else:
                    do = "%QX" + str(100 + (counter_do // 8)) + "." + str(counter_do%8) + " to "
                    counter_do += row[4];
                    do += "%QX" + str(100 + ((counter_do-1) // 8)) + "." + str((counter_do-1)%8)
                    
                #calculate ai
                if (row[5] + row[6] == 0):
                    ai = "-"
                else:
                    ai = "%IW" + str(100 + counter_ai) + " to "
                    counter_ai += row[5]+row[6];
                    ai += "%IW" + str(100 + (counter_ai-1))
                    
                #calculate ao
                if (row[7] == 0):
                    ao = "-"
                else:
                    ao = "%QW" + str(100 + counter_ao) + " to "
                    counter_ao += row[7];
                    ao += "%QW" + str(100 + (counter_ao-1))
                
        except Error as e:
            print("error connecting to the database" + str(e))
    else:
        pass            

def sanitize_input(*args):
   return (escape(a) for a in args)

#----------------------------------------------------------------------------
# Taken from the html module of the python 3.9 standard library
# exact lines of code can be found here:
# https://github.com/python/cpython/blob/3.9/Lib/html/__init__.py#L12
# Modified to convert to String but preserve NoneType.
# Preserving NoneType is necessary to ensure program logic is not affected by None being converted to "None",
# this is relevant in setttings()
#----------------------------------------------------------------------------
def escape(s, quote=True):
    """
    Replace special characters "&", "<" and ">" to HTML-safe sequences.
    If the optional flag quote is true (the default), the quotation mark
    characters, both double quote (") and single quote (') characters are also
    translated.
    """
    if s is None: 
        return s
    s = str(s) # force string
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
        s = s.replace('\'', "&#x27;")
    return s


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="A simple script to demonstrate command-line argument parsing."
    )

    parser.add_argument(
        "--action",
        help="Compile a program or start the PLC"
    )

    parser.add_argument(
        "--input_file",
        help="Path to the st file that needs processing."
    )

    args = parser.parse_args()

    #openplc_runtime.start_runtime()

    if args.action == 'compile':
        #file = open(args.input_file, "r")
        #st_file = file.read()
        #st_file = st_file.replace('\r','').replace('\n','')

        compile_program(st_file=args.input_file)

    elif args.action == 'execute':
        
        st_file = args.input_file
        
        database = "openplc.db"
        conn = create_connection(database)
        if (conn != None):
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM Programs WHERE File=?", (st_file,))
                #cur.execute("SELECT * FROM Programs")
                row = cur.fetchone()
                openplc_runtime.project_name = str(row[1])
                openplc_runtime.project_description = str(row[2])
                openplc_runtime.project_file = str(row[3])
                
                cur.execute("SELECT * FROM Settings")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                
                for row in rows:
                    if (row[0] == "Start_run_mode"):
                        start_run = str(row[1])
                        
                if (start_run == 'true'):
                    print("Initializing OpenPLC in RUN mode...")
                    openplc_runtime.start_runtime()
                    time.sleep(1)
                    configure_runtime()
                    #monitor.parse_st(openplc_runtime.project_file)
                            
            except Error as e:
                print("error connecting to the database" + str(e))
        else:
            print("error connecting to the database")

    else:
        pass


