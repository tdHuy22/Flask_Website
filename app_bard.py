import subprocess
import time
import threading
from flask import Flask, request, render_template

app = Flask(__name__)

# Function to check internet connection
def check_internet_connection():
    process = subprocess.Popen(['ping', '8.8.8.8', '-c', '1', '-t', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error) = process.communicate()
    return error.decode('utf-8').find('packet loss rate') == -1

# Function to get the IP address
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

# Function to turn on access point
def start_access_point():
    subprocess.run(['sudo', 'service', 'dhcpcd', 'stop'])
    subprocess.run(['sudo', 'systemctl', 'disable', 'dhcpcd'])
    
    subprocess.run(['sudo', 'systemctl', 'enable', 'NetworkManager'])
    subprocess.run(['sudo', 'service', 'NetworkManager', 'start'])
    
    subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'hotspot', 'ifname', 'wlan0', 'con-name', 'UTK_Converter','ssid', 'RPI_Zero', 'password', 'RPI012345'])
    

# Function to stop access point
def stop_access_point():
    
    subprocess.run(['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'])
    
    subprocess.run(['sudo', 'service', 'NetworkManager', 'stop'])
    subprocess.run(['sudo', 'systemctl', 'disable', 'NetworkManager'])
    
    subprocess.run(['sudo', 'systemctl', 'enable', 'dhcpcd'])
    subprocess.run(['sudo', 'service', 'dhcpcd', 'start'])

# Function to scan WiFi networks and store them in a list
def scan_wifi():
    WiFi_List = []
    process = subprocess.Popen(['sudo', 'iwlist', 'wlan0', 'scan'], stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8')
    lines = output.split('\n')

    for line in lines:
        if line.startswith('ESSID:'):
            SSID = line.split(':')[1].strip('"')
            WiFi_List.append(SSID)

    return WiFi_List

# Function to connect to a specific WiFi network
def connect_wifi(SSID, password):
    process = subprocess.Popen(['sudo', 'wpa_supplicant', '-i', 'wlan0', '-c', '/etc/wpa_supplicant/wpa_supplicant.conf'], stdout=subprocess.PIPE)
    process.communicate()

    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
        f.write('[network]\n')
        f.write('ssid="{}\n'.format(SSID))
        f.write('psk="{}\n'.format(password))

    process = subprocess.Popen(['sudo', 'dhcpcd', 'wlan0'], stdout=subprocess.PIPE)
    process.communicate()

# Route for displaying the list of scanned WiFi networks
@app.route('/')
def wifi_list():
    WiFi_List = scan_wifi()
    return render_template('wifi_list.html', WiFi_List=WiFi_List)

# Route for connecting to a selected WiFi network
@app.route('/connect', methods=['POST'])
def connect():
    SSID = request.form['SSID']
    password = request.form['password']

    process = subprocess.Popen(['sudo', 'wpa_cli', '-i', 'wlan0', 'scan'], stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8')
    lines = output.split('\n')

    if not any(SSID.startswith(line.split(':')[1].strip('"')) for line in lines):
        return render_template('failed.html')

    connect_wifi(SSID, password)
    return render_template('success.html')

def main():
    while True:
        if check_internet_connection():
            print('Internet is connected')
            return

        start_access_point()
        print('Access point turned on')

        # Start Flask server in a separate thread
        threading.Thread(target=app.run(host='0.0.0.0', port=5000)).start()

        # Wait for internet connection
        while not check_internet_connection():
            time.sleep(1)

        # Stop access point
        stop_access_point()
        print('Access point turned off')
        print('Internet is connected')

if __name__ == '__main__':
    main()
