from flask import Flask, jsonify, request
import requests
import concurrent.futures
import time
import json
import socket

app = Flask(__name__)

# API endpoints configuration for Lambda and EC2
LAMBDA_API_URL = "https://1s32of1o09.execute-api.us-east-1.amazonaws.com"
LAMBDA_FUNCTION_PATH = "/default/CLOUD_LAMBDA"
EC2_API_URL = "https://67xydz76j6.execute-api.us-east-1.amazonaws.com"
EC2_FUNCTION_PATH = "/default/EC2_CONNECTION"

@app.route('/warmup', methods=['GET','POST'])
def warmup():
    if request.method == 'POST':
        req_data = request.get_json()
        global selected_service
        global total_warmup_time
        global warmup_responses
        global resource_count
        global warmup_cost
        warmup_durations = []

        if req_data['service'] == 'lambda':
            warmup_responses = []
            resource_count = int(req_data['resources'])
            selected_service = 'lambda'
            print(resource_count)
           
            def call_lambda_instance(_):
                try:
                    start_time = time.time()
                    response = requests.post(LAMBDA_API_URL + LAMBDA_FUNCTION_PATH)
                    response.raise_for_status()
                    print(f"Lambda instance called: {response.status_code}")
                    print("Elapsed Time:", time.time() - start_time)
                    warmup_durations.append(time.time() - start_time)
                    warmup_responses.append(response)
                except Exception as e:
                    print(f"Error calling Lambda instance: {e}")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(call_lambda_instance, range(resource_count))
            print(warmup_durations)
            total_warmup_time = sum(warmup_durations)
            print(total_warmup_time)
            warmup_cost = str((total_warmup_time / 60) * 0.0134)
           
            return jsonify({"result": "ok"})
       
        elif req_data['service'] == 'ec2':
            resource_count = int(req_data['resources'])
            print(req_data)
            body = json.dumps({"num_resources": resource_count})
            headers = {'Content-Type': 'application/json'}
            warmup_responses = []
            selected_service = 'ec2'
           
            def start_ec2_instances():
                try:
                    start_time = time.time()
                    response = requests.post(EC2_API_URL + EC2_FUNCTION_PATH, headers=headers, data=body, verify=True)
                    time.sleep(10)
                    print(response)
                    data = response.json()
                    if response.status_code == 200:
                        warmup_responses.append(data)
                    else:
                        return "Error calling EC2"
                    print("Elapsed Time:", time.time() - start_time)
                    warmup_durations.append(time.time() - start_time)
                    print(f"EC2 instances started")
                except Exception as e:
                    print(f"Error starting EC2 instances: {e}")

            start_ec2_instances()
            total_warmup_time = sum(warmup_durations)
            print(total_warmup_time)
            warmup_cost = str((total_warmup_time / 3600) * resource_count * 0.012)
           
            return jsonify({"result": "ok"})

@app.route('/scaled_ready', methods=['GET','POST'])
def scaled_ready():
    if request.method == 'GET':
        if selected_service == "ec2":
            if resource_count == len(warmup_responses[0]):
                print(warmup_responses)
                print(resource_count)
                return jsonify({"ready": True})
            else:
                print(warmup_responses)
                print(resource_count)
                return jsonify({"ready": False})
        else:
            if resource_count == len(warmup_responses):
                print(warmup_responses)
                print(resource_count)
                return jsonify({"ready": True})
            else:
                print(warmup_responses)
                print(resource_count)
                return jsonify({"ready": False})

@app.route('/get_warmup_cost', methods=['GET','POST'])
def get_warmup_cost():
    if request.method == 'GET':
        return jsonify({"total_time": total_warmup_time, "cost": warmup_cost})

@app.route('/get_endpoints', methods=['GET','POST'])
def get_endpoints():
    if request.method == 'GET':
        endpoints = []
        endpoint_map = {}
        if selected_service == "ec2":
            for instance in warmup_responses:
                for item in instance:
                    if 'PublicDnsName' in item:
                        endpoints.append("http://" + str(item['PublicDnsName']) + "/")
            for i in range(len(endpoints)):
                endpoint_map[f"resource_{i}"] = endpoints[i]
            return endpoint_map
        else:
            return "No endpoints for Lambda."

@app.route('/analyse', methods=['GET','POST'])
def analyse():
    if request.method == 'POST':
        data = request.get_json()
        if not data or not all(k in data for k in ('history', 'datapoints', 'buy_sell', 'profit_days')):
            return jsonify({"error": "Missing one or more required data parameters"}), 400

        h = int(data['history'])
        d = int(data['datapoints'])
        t = "1" if str(data['buy_sell']) == "buy" else "0"
        p = int(data['profit_days'])
        analysis_body = json.dumps({"minhistory": h, "shots": d, "bs": t, "profit_loss_days": p})
        analysis_data = {"minhistory": h, "shots": d, "bs": t, "profit_loss": p}
        global analysis_responses
        global analysis_time
        global analysis_cost
        global risk_95
        global risk_99
        global avg_risk_95
        global avg_risk_99
        global exec_time
        global exec_cost
        analysis_responses = []
        global sorted_analysis_data
        global total_profit
        if selected_service == "lambda":
            start_time = time.time()
            def invoke_lambda_for_analysis(_):
                try:
                    response = requests.post(LAMBDA_API_URL + LAMBDA_FUNCTION_PATH, data=analysis_body, verify=False)
                    print(response.json())
                    return response.json()
                except Exception as e:
                    print(f"Error invoking Lambda instance for analysis: {e}")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                analysis_responses = list(executor.map(invoke_lambda_for_analysis, range(resource_count)))
            analysis_time = time.time() - start_time
            analysis_cost = str((analysis_time / 60) * 0.0134)

        if selected_service == "ec2":
            urls = []
            ip_addresses = []
            start_time = time.time()
            headers = {'Content-Type': 'application/json'}
            for instance in warmup_responses:
                for item in instance:
                    if 'PublicIpAddress' in item:
                        ip_addresses.append(item['PublicIpAddress'])
                        urls.append("http://" + item['PublicIpAddress'] + ":80")
            print(urls)
            for ip in ip_addresses:
                if is_connected(ip) == 1:
                    print("connected")
                    time.sleep(10)
                    connect_url = "http://" + ip + ":80"
                    response = requests.post(connect_url, headers=headers, json=analysis_data, verify=True, timeout=600)
                    analysis_responses.append(response.json())
            analysis_time = time.time() - start_time
            analysis_cost = str((analysis_time / 3600) * resource_count * 0.012)

        data_list = [response["data"] for response in analysis_responses]
        flattened_data = [item for sublist in data_list for item in sublist]
        sorted_analysis_data = sorted(flattened_data, key=lambda x: x['date'])

        print(sorted_analysis_data)

        risk_95 = []
        risk_99 = []

        for item in flattened_data:
            risk_95.append(item["95%"])
            risk_99.append(item["99%"])
        avg_risk_95 = sum(risk_95) / len(risk_95)
        avg_risk_99 = sum(risk_99) / len(risk_99)

        profit_loss_values = []
        for item in flattened_data:
            profit_loss_values.append(item["Profit/Loss"])
        total_profit = sum(profit_loss_values)

        exec_time = total_warmup_time + analysis_time
        exec_cost = float(warmup_cost) + float(analysis_cost)

        headers = {'Content-Type': 'application/json'}
        audit_data = {"service": selected_service, "resources": resource_count, "history": h, "datapoints": d, "buy_sell": t, "profit_days": p, "total_profit": total_profit, "avg_95": avg_risk_95, "avg_99": avg_risk_99, "execution_time": exec_time, "execution_cost": exec_cost}
        audit_body = json.dumps(audit_data)
        response = requests.post("https://e3u6ekg70l.execute-api.us-east-1.amazonaws.com/default/AuditData", headers=headers, data=audit_body, verify=True, timeout=600)

        return {"result": "ok"}

def is_connected(ip):
    retries = 10
    retry_delay = 10
    retry_count = 0
    while retry_count <= retries:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(10)
        result = sock.connect_ex((ip, 80))
        if result == 0:
            print("Instance is UP & accessible on port 80")
            return 1
        else:
            print("Instance is still down, retrying . . .")
            return is_connected(ip)

@app.route('/get_sig_vars9599', methods=['GET','POST'])
def get_sig_vars9599():
    if request.method == 'GET':
        if sorted_analysis_data is None:
            return "Data has been reset, please run the analysis again."
        first_20_by_date = sorted_analysis_data[:20]

        response_data = {"var95": [], "var99": []}
        for entry in first_20_by_date:
            response_data["var95"].append(entry["95%"])
            response_data["var99"].append(entry["99%"])

        return response_data

@app.route('/get_avg_vars9599', methods=['GET','POST'])
def get_avg_vars9599():
    if request.method == 'GET':
        if avg_risk_95 is None and avg_risk_99 is None:
            return "Data has been reset, please run the analysis again."
        return {"var95": avg_risk_95, "var99": avg_risk_99}

@app.route('/get_sig_profit_loss', methods=['GET','POST'])
def get_sig_profit_loss():
    if request.method == 'GET':
        if sorted_analysis_data is None:
            return "Data has been reset, please run the analysis again."
        response_data = {"profit_loss": []}
        last_20_by_date = sorted_analysis_data[-20:]
        for entry in last_20_by_date:
            response_data["profit_loss"].append(entry["Profit/Loss"])
        return response_data

@app.route('/get_tot_profit_loss', methods=['GET','POST'])
def get_tot_profit_loss():
    if request.method == 'GET':
        if total_profit is None:
            return "Data has been reset, please run the analysis again."
        return {"profit_loss": total_profit}

@app.route('/get_chart_url', methods=['GET','POST'])
def get_chart_url():
    if request.method == 'GET':
        var95_list = []
        var99_list = []
        dates_list = []
        global chart_url
        if analysis_responses is None:
            return "Data has been reset, please run the analysis again."
        data_list = [response["data"] for response in analysis_responses]
        flattened_data = [item for sublist in data_list for item in sublist]
        for entry in flattened_data:
            var95_list.append(entry["95%"])
            var99_list.append(entry["99%"])
            dates_list.append(entry["date"])
        avg_var95 = sum(var95_list) / len(var95_list)
        avg_var99 = sum(var99_list) / len(var99_list)

        avg_var95_list = [avg_var95] * len(var95_list)
        avg_var99_list = [avg_var99] * len(var99_list)

        date_str = '|'.join(dates_list)
        var95_str = ','.join([str(i) for i in var95_list])
        avg95_str = ','.join([str(avg_var95) for i in range(len(dates_list))])
        var99_str = ','.join([str(i) for i in var99_list])
        avg99_str = ','.join([str(avg_var99) for i in range(len(dates_list))])
        labels = "95%RiskValue|99%RiskValue|Average95%|Average99%"

        chart_url = f"https://image-charts.com/chart?cht=lc&chs=999x499&chd=a:{var95_str}|{var99_str}|{avg95_str}|{avg99_str}&chxt=x,y&chdl={labels}&chxl=0:|{date_str}&chxs=0,min90&chco=1984C5,C23728,A7D5ED,E1A692&chls=3|3|3,5,3|3,5,3"
       
        return {"url": chart_url}

@app.route('/get_time_cost', methods=['GET','POST'])
def get_time_cost():
    if request.method == 'GET':
        if exec_time is not None and exec_cost is not None:
            return {"time": exec_time, "cost": exec_cost}
        else:
            return "Data has been reset, please run the analysis again."

@app.route('/get_audit', methods=['GET','POST'])
def get_audit():
    if request.method == 'GET':
        global audit_response
        audit_response = requests.post("https://wdi9w7gmv7.execute-api.us-east-1.amazonaws.com/default/showAuditData")
        audit_result = audit_response.json()
        print(audit_result)
        return audit_result

@app.route('/reset', methods=['GET','POST'])
def reset():
    if request.method == 'GET':
        global total_warmup_time, warmup_responses, resource_count, h, d, t, p, total_profit, avg_risk_95, avg_risk_99, exec_time, exec_cost, warmup_cost, analysis_time, sorted_analysis_data, analysis_responses, analysis_cost, audit_response

        total_warmup_time = None
        warmup_responses = None
        resource_count = None
        h = None
        d = None
        t = None
        p = None
        total_profit = None
        avg_risk_95 = None
        avg_risk_99 = None
        exec_time = None
        exec_cost = None
        warmup_cost = None
        analysis_time = None
        sorted_analysis_data = None
        analysis_responses = None
        analysis_cost = None
        audit_response = None
        return {"result": "ok"}

@app.route('/terminate', methods=['GET','POST'])
def terminate():
    if request.method == 'GET':
        global termination_status
        headers = {'Content-Type': 'application/json'}
        active_instances = []
        print(warmup_responses)
        if selected_service == "ec2":
            for instance in warmup_responses:
                for item in instance:
                    if 'InstanceId' in item:
                        active_instances.append(item['InstanceId'])
                    else:
                        return {"terminated": "true"}
            active_instances_str = str(active_instances)
            body = json.dumps({"instances": active_instances_str})
            response = requests.post("https://2ovesrs65e.execute-api.us-east-1.amazonaws.com/default/terminate", headers=headers, data=body, verify=True)
            response_json = response.json()
            if "ResponseMetadata" in response_json:
                termination_status = "ok"
                return {"result": "ok"}
         
        if selected_service == "lambda":
            termination_status = "ok"
            return {"result": "ok"}

@app.route('/scaled_terminated', methods=['GET','POST'])
def scaled_terminated():
    if request.method == 'GET':
        if termination_status == "ok":
            return {"terminated": "true"}
        else:
            return {"terminated": "false"}

if __name__ == '__main__':
    app.run(debug=True)
