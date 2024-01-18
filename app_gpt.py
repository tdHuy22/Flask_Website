import subprocess
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

WiFi_List = []
WPA_List = []

def check_internet_connection():
    try:
        # Check internet connectivity by pinging Google's DNS server
        print("Check Internet Connection")
        subprocess.check_output(['ping', '-c', '1', '8.8.8.8'])
        return True
    except subprocess.CalledProcessError:
        return False
   
def get_ip_address():
    try:
        # Run the 'hostname -I' command to get the IP address
        result = subprocess.check_output(['hostname', '-I'])
        
        # Decode the byte result to a string and extract the IP address
        ip_address = result.decode('utf-8').strip().split()[0]

        return ip_address
    except Exception as e:
        print(f"Error: {e}")
        return None

def turn_on_access_point():
    # Enable the access point with a specific SSID and password -- OLD VERSION
    # subprocess.run(['sudo', 'systemctl', 'start', 'hostapd'])
    # subprocess.run(['sudo', 'systemctl', 'start', 'dnsmasq'])
    print("Turn on access point")
    # Enable the access point with a specific SSID and password -- NEW VERSION
    subprocess.run(['sudo', 'service', 'dhcpcd', 'stop'])
    # subprocess.run(['sudo', 'systemctl', 'disable', 'dhcpcd'])
    # time.sleep(1)
    # subprocess.run(['sudo', 'systemctl', 'enable', 'NetworkManager'])
    subprocess.run(['sudo', 'service', 'NetworkManager', 'start'])
    # time.sleep(1)
    #subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'hotspot', 'ifname', 'wlan0', 'con-name', 'UTK_Converter','ssid', 'RPI_Zero', 'password', 'RPI012345'])
    subprocess.run(['sudo', 'nmcli', 'device', 'connect', 'wlan0'])
    # time.sleep(1)
 
def turn_off_access_point():
    # Disable the access point
    print("Turn off access point")
    subprocess.run(['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'])
    
    subprocess.run(['sudo', 'service', 'NetworkManager', 'stop'])
    # subprocess.run(['sudo', 'systemctl', 'disable', 'NetworkManager'])
    # time.sleep(1)
    # subprocess.run(['sudo', 'systemctl', 'enable', 'dhcpcd'])
    subprocess.run(['sudo', 'service', 'dhcpcd', 'start'])
    # time.sleep(1)
    
@app.route('/')
def index():
    return render_template('index.html', WiFi_List=WiFi_List)

@app.route('/scan')
def scan():
    WiFi_List.clear()

    # Use subprocess to execute the 'iwlist' command to scan for Wi-Fi networks
    scan_output = subprocess.check_output(['sudo', 'iwlist', 'wlan0', 'scan']).decode('utf-8')
    # Parse the scan output to extract Wi-Fi networks
    
    lines = scan_output.split('\n')
    for line in lines:
        if 'ESSID' in line:
            wifi_name = line.split('"')[1]
            WiFi_List.append(wifi_name)

    return redirect(url_for('index'))

@app.route('/connect', methods=['POST'])
def connect():
    selected_wifi = request.form['wifi']
    password = request.form['password']

    turn_off_access_point()    
    # Use subprocess to connect to the selected Wi-Fi network
    
    try:
        network_id = WPA_List.index(selected_wifi)
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'set_network', network_id, 'psk', f'"{password}"'])
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'enable_network', network_id])
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'save_config'])
    except ValueError:
        connect_output = subprocess.check_output(['sudo', 'wpa_cli', '-i', 'wlan0', 'add_network']).decode('utf-8')
        network_id = connect_output.strip()

        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'set_network', network_id, 'ssid', f'"{selected_wifi}"'])
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'set_network', network_id, 'psk', f'"{password}"'])
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'enable_network', network_id])
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'save_config'])
        
        WPA_List.append(selected_wifi)
        
    
    time.sleep(10)  # Allow time for the connection to be established

    if check_internet_connection():
        print("Internet is connected")
        return "Internet is connected"
    else:
        turn_on_access_point()
        return redirect(url_for('index'))

if __name__ == '__main__':
    # if check_internet_connection():
    #     print("Internet is connected")
    # else:
    #     turn_on_access_point()
        app.run(host='0.0.0.0', port=5050, debug=True)
