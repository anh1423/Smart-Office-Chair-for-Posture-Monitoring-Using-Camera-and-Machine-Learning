# Node-RED Flow Configuration Guide

Complete guide for creating Node-RED flows to integrate ESP32, Webserver, and MQTT.

## Flow Overview

```
ESP32 → MQTT → Node-RED → HTTP POST → Webserver → HTTP Response → Node-RED → MQTT → ESP32
```

## Quick Import

Copy this JSON and import into Node-RED (Menu → Import → Clipboard):

**Note**: See `flow_1_posture_detection.json` and `flow_2_battery_monitoring.json` for complete flow files.

---

## Configuration Details

### 1. MQTT In Node (ESP32 Sensor Data)

**Configuration:**
- **Server**: `localhost:1883` (MQTT broker on Pi5)
- **Topic**: `esp32/fsrsensor`
- **QoS**: 0
- **Output**: Parsed JSON object

**Data received from ESP32:**
```json
{
  "sensor1": 100.5,
  "sensor2": 150.2,
  "sensor3": 120.8,
  "sensor4": 180.3,
  "sensor5": 95.7,
  "sensor6": 110.4,
  "sensor7": 140.9
}
```

---

### 2. Function Node: Prepare API Request

**Code:**
```javascript
// msg.payload is already a JSON object from ESP32
// Forward directly to HTTP request

// Log for debugging
node.warn("Received sensor data: " + JSON.stringify(msg.payload));

return msg;
```

---

### 3. HTTP Request Node

**⚠️ IMPORTANT: API Key Required**

Starting from the latest version, the `/api/predict` endpoint requires API key authentication for security.

**Generate API Key:**
```bash
cd /home/pi/webserver
python3 generate_api_key.py
```

Follow the prompts to create an API key. **Save the key securely** - you will only see it once!

**Configuration:**
- **Method**: POST
- **URL**: 
  - Development: `http://192.168.101.XXX:5000/api/predict`
  - Production: `http://localhost:5000/api/predict`
- **Return**: Parsed JSON object
- **Headers**: 
  - `Content-Type: application/json` (automatic)
  - **`X-API-Key: <your-api-key-here>`** ⚠️ **REQUIRED**

**How to add API Key header in Node-RED:**
1. Double-click HTTP Request node
2. Click "Add new header" button
3. Set header name: `X-API-Key`
4. Set header value: paste your API key (64 characters)
5. Click Done

**Alternative: Use environment variable**
```javascript
// In HTTP Request node, set header value to:
${API_KEY}

// Then set environment variable in Node-RED settings.js:
functionGlobalContext: {
    API_KEY: "your-api-key-here"
}
```

**Request body**: Automatically from `msg.payload`

**Response received:**
```json
{
  "label": "Correct_posture",
  "confidence": 0.95,
  "warning": false,
  "mode": "auto",
  "timestamp": "2025-12-02T15:30:00",
  "metadata": {...}
}
```

---

### 4. Function Node: Parse Response

**Code:**
```javascript
// msg.payload from webserver
var result = {
    label: msg.payload.label,
    warning: msg.payload.warning,
    confidence: msg.payload.confidence,
    mode: msg.payload.mode
};

// Log for debugging
node.warn("Prediction result: " + JSON.stringify(result));

msg.payload = result;
return msg;
```

---

### 5. MQTT Out Node (Send to ESP32)

**Configuration:**
- **Server**: `localhost:1883`
- **Topic**: `esp32/recognitionresult`
- **QoS**: 0
- **Retain**: false

**Data sent:**
```json
{
  "label": "Upper_body_hunched",
  "warning": true,
  "confidence": 0.88,
  "mode": "auto"
}
```

---

## MQTT Broker Setup

### Install Mosquitto on Pi5

```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients

# Enable and start service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### Create MQTT User

```bash
# Create password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd mqttadmin

# Enter password: mqttadmin
```

### Configure Mosquitto

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add to end of file:
```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
```

### Test MQTT

```bash
# Subscribe (terminal 1)
mosquitto_sub -h localhost -t "esp32/#" -u mqttadmin -P mqttadmin -v

# Publish (terminal 2)
mosquitto_pub -h localhost -t "esp32/test" -u mqttadmin -P mqttadmin -m "Hello MQTT"
```

---

## Testing the Flow

### 1. Test with MQTT Publish

```bash
# Send simulated data from ESP32
mosquitto_pub -h localhost -t "esp32/fsrsensor" -u mqttadmin -P mqttadmin \
  -m '{"sensor1": 100, "sensor2": 150, "sensor3": 120, "sensor4": 180, "sensor5": 95, "sensor6": 110, "sensor7": 140}'
```

### 2. Check Debug Log

In Node-RED:
- Open Debug sidebar (bug icon)
- View output from function nodes

### 3. Subscribe to Results

```bash
# Listen for results sent back to ESP32
mosquitto_sub -h localhost -t "esp32/recognitionresult" -u mqttadmin -P mqttadmin -v
```

---

## Troubleshooting

### Error: MQTT connection refused

**Check:**
```bash
sudo systemctl status mosquitto
sudo netstat -tlnp | grep 1883
```

### Error: HTTP request timeout

**Check:**
```bash
# Is webserver running?
curl http://localhost:5000/api/health

# Or from another machine
curl http://192.168.101.192:5000/api/health
```

### Error: Invalid JSON from ESP32

**Debug:**
- View debug output from function node
- Check JSON format from ESP32

---

## Advanced: Error Handling

Add error handling to flow:

```javascript
// In function_prepare_request
try {
    // Validate sensor data
    for (let i = 1; i <= 7; i++) {
        let key = 'sensor' + i;
        if (typeof msg.payload[key] !== 'number') {
            throw new Error('Invalid sensor data: ' + key);
        }
    }
    return msg;
} catch (error) {
    node.error(error.message, msg);
    return null; // Stop flow
}
```

```javascript
// In function_parse_response
try {
    if (!msg.payload || !msg.payload.label) {
        throw new Error('Invalid response from webserver');
    }
    
    var result = {
        label: msg.payload.label,
        warning: msg.payload.warning || false,
        confidence: msg.payload.confidence || 0,
        mode: msg.payload.mode || 'unknown'
    };
    
    msg.payload = result;
    return msg;
} catch (error) {
    node.error(error.message, msg);
    // Send error to ESP32
    msg.payload = {
        label: 'Error',
        warning: true,
        confidence: 0,
        mode: 'error'
    };
    return msg;
}
```

---

## Monitoring

### Add Debug Nodes

Add debug nodes after each function to monitor:
- After MQTT In: View data from ESP32
- After HTTP Request: View response from webserver
- Before MQTT Out: View data sent to ESP32

### Log to File (Optional)

Add file output node to log:
```javascript
// Function node
var logEntry = {
    timestamp: new Date().toISOString(),
    sensor_data: msg.payload,
    result: msg.result
};

msg.payload = JSON.stringify(logEntry) + '\n';
msg.filename = '/home/pi/nodered_logs/posture_' + 
               new Date().toISOString().split('T')[0] + '.log';

return msg;
```

---

## Dashboard Integration (Optional)

Install node-red-dashboard:
```bash
cd ~/.node-red
npm install node-red-dashboard
```

Restart Node-RED and add dashboard nodes to visualize real-time data.

---

## Battery Monitoring Flow

For battery monitoring from ESP32, use similar flow:

**MQTT Topic**: `esp32/battery`

**Data format:**
```json
{
  "voltage": 4.2,
  "percentage": 95,
  "status": "charging"
}
```

**API Endpoint**: `POST /api/battery`

See `flow_2_battery_monitoring.json` for complete implementation.

---

## Security Notes

1. **Change default MQTT password** in production
2. **Use TLS/SSL** for MQTT in production
3. **Secure API keys** - never commit to git
4. **Firewall rules** - restrict MQTT port access

---

## References

- **Flow Files**: 
  - `flow_1_posture_detection.json`
  - `flow_2_battery_monitoring.json`
  - `nodered_flow_with_apikey.json`
- **API Key Guide**: See README.md
- **Deployment**: See PI5_DEPLOYMENT_GUIDE.md

---

**Happy integrating! 🚀**
