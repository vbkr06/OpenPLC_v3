
import os
import subprocess
import openplc
import monitoring as monitor
import time
import argparse
import random

openplc_runtime = openplc.runtime()

def start_plc():
    global openplc_runtime
    
    monitor.stop_monitor()
    openplc_runtime.start_runtime()
    time.sleep(1)
    monitor.cleanup()
    monitor.parse_st(openplc_runtime.project_file)


def stop_plc():
    global openplc_runtime
    
    openplc_runtime.stop_runtime()
    time.sleep(1)
    monitor.stop_monitor()


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
        pass
    else:
        pass


