import requests, json, certifi, pprint, os, time, csv

requests.packages.urllib3.disable_warnings() 

# Setup - Read from environment variables
with open(r"C:\code\SAS_MCP\access_server.txt", "r") as f:
    sasserver = f.read().strip()
# Access token from file
with open(r"C:\code\SAS_MCP\access_token.txt", "r") as f:
    access_token = f.read().strip()

# Pretty printer for better output readability
pp = pprint.PrettyPrinter(indent=2)

def test_connection():
    """
    Runs a request against the My Folder of the user to check the connection

    Returns
    -------
    None on failure and a dictionary on success
    """
    print("Testing connectivity to user's home folder (@myFolder)...")
    # Use @myFolder which typically resolves to the logged-in user's home folder
    url = sasserver + "/folders/folders/@myFolder"
    headers = {'Authorization': 'Bearer ' + access_token}
    
    try:
        response = requests.request("GET", url, headers=headers, verify=False) #certifi.where()
        print(f"Status code for @myFolder: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Connection and access to @myFolder successful!")
            return data
        elif response.status_code == 404:
            print("Connection successful, but @myFolder not found or accessible.")
            print("Check user permissions or if the home folder exists.")
            print(f"Response: {response.text}")
            return None
        else:
            print(f"Connection or access failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {str(e)}")
        return None

def get_compute_context_uuid(compute_context_name):
    """
    Returns the UUID of a specified compute context.

    Parameters
    ----------
    compute_context_name : str
        Contains the name of the target compute context.
    
    Returns
    -------
    str
        The string contains the Compute Context UUID, which is used to create a SAS Session.
    """
    print(f"Retrieving the UUID of the compute context {compute_context_name}")
    url = sasserver + f"/compute/contexts?filter=eq(name,'{compute_context_name}')"
    headers = {'Authorization': 'Bearer ' + access_token}
    try:
        response = requests.request('GET', url, headers=headers, verify=False)#certifi.where()
        
        if response.status_code == 200:
            data = response.json()
            print("Compute Context UUID was retrieved successfully!")
            return data['items'][0]['id']
        else:
            print(f"Failed to get server info: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting server info: {str(e)}")
        return None

def create_sas_session(compute_context_name='SAS Studio compute context'):
    """
    Create a SAS Session.

    Parameters
    ----------
    compute_context_name : str, optional
        Contains the name of the target compute context. Defaults to SAS Studio compute context.
    
    Returns
    -------
    str
        The string contains the SAS Session UUID, which is used to submit code against it.
    """
    # First step to starting a SAS Session is getting the UUID for the Compute Context
    compute_context_uuid = get_compute_context_uuid(compute_context_name)
    
    if compute_context_uuid != None:
        print('Starting SAS Session')
        url = sasserver + f"/compute/contexts/{compute_context_uuid}/sessions"
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
            }
        payload = json.dumps({
            "version": 1,
            "name": "MCP",
            "description": "This is a MCP session",
            "attributes": {},
            "environment": {
                "options": [
                "memsize=4g",
                "fullstimer"
                ]
            }
        })
        try:
            response = requests.request('POST', url, headers=headers, data=payload, verify=False)#certifi.where()
            if response.status_code == 201:
                data = response.json()
                print("A SAS Session was successfully started!")
                sas_session_id = data['id']
                return sas_session_id
            else:
                print(f"Failed to start a SAS Session: {response.text}")
                return None
        except:
            print('Unable to create a SAS Session')
            return None
    else:
        return None
    
def submit_sas_code(session, sas_code=['%put Hello World;']):
    """
    Submit SAS Code to a SAS session

    Parameters
    ----------
    session : str
        UUID for the session to submit code to.
    sas_code : list of strings, optional
        List of SAS Code statements.
    
    Returns
    -------
    str
        The string contains the SAS Job UUID, which is used to monitor the running code.
    """
    print('Submitting SAS Code to the SAS Session')
    url = sasserver + f"/compute/sessions/{session}/jobs"
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        "version": 1,
        "name": "mcp",
        "description": "Submitting code from MCP",
        "code": sas_code,
        "attributes": {
            "resetLogLineNumbers": True
        }
    })
    try:
        response = requests.request('POST', url, headers=headers, data=payload, verify=False)#certifi.where()
        if response.status_code == 201:
            data = response.json()
            print("SAS code was submitted successfully!")
            sas_session_job_id = data['id']
            return sas_session_job_id
        else:
            print(f"Failed to submit SAS: {response.text}")
            return None
    except:
        print('Unable to submit SAS code')
        return None

def check_job_submission_status(session, job):
    """
    Check the submission status of a SAS job.

    Parameters
    ----------
    session : str
        UUID for the session to submit code to.
    job : str
        UUID for the job.
    
    Returns
    -------
    str
        The string contains the result status of the submitted job.
    """
    print('Checking Status of the submitted SAS code')
    time.sleep(5)
    url = sasserver + f"/compute/sessions/{session}/jobs/{job}/state"
    headers = {'Authorization': 'Bearer ' + access_token}
    try:
        response = requests.request('GET', url, headers=headers, verify=False)#certifi.where()
        if response.status_code == 200:
            if response.text in ['pending', 'running']:
                check_job_submission_status(session, job)
            else:
                if response.text in ['canceled']:
                    print('The code submission was cancled. Please retry.')
                    return None
                else:
                    print('SAS code was submitted successfully!')
                    return response.text
        else:
            print(f"Failed to retrieve SAS code submission state: {response.text}")
            return None
    except:
        print('Unable to retrieve SAS code submission state.')
        return None

def get_job_results(session, job, result_types=['log', 'results', 'data'], library='work', table='results'):
    """
    Check the submission status of a SAS job.

    Parameters
    ----------
    session : str
        UUID for the session to submit code to.
    job : str
        UUID for the job.
    result_types: list, optional
        Contains a list of result types the user is interested - can be:
        - log, to get the log file
        - results, to get the ODS results
        - data, retrieves a specified table
    library : str, optional
        Specify the name of the library of the table that you want to retrieve - default is work
    table : str, optional
        Specify the name of the table that you want to retrieve - default is results
    
    Returns
    -------
    object
        Contains attributes corresponding to the result_types.
    """
    results_objects = {}
    if 'log' in result_types:
        url = sasserver + f"/compute/sessions/{session}/jobs/{job}/log?limit=100000"
        headers = {'Authorization': 'Bearer ' + access_token}
        try:
            response = requests.request('GET', url, headers=headers, verify=False)#certifi.where()
            if response.status_code == 200:
                data = response.json()
                results_objects['log'] = data['items']
                print('SAS log was retrieved successfully!')
            else:
                print(f"Failed to retrieve SAS log: {response.text}")
        except:
            print('Unable to retrieve SAS log.')

    if 'results' in result_types:
        url = sasserver + f"/compute/sessions/{session}/jobs/{job}/results?limit=100000"
        headers = {'Authorization': 'Bearer ' + access_token}
        try:
            response = requests.request('GET', url, headers=headers, verify=False)#certifi.where()
            if response.status_code == 200:
                data = response.json()
                results_objects['results'] = data['items']
                print('SAS results was retrieved successfully!')
            else:
                print(f"Failed to retrieve SAS results: {response.text}")
        except:
            print('Unable to retrieve SAS results.')
    
    if 'data' in result_types:
        url = sasserver + f"/compute/sessions/{session}/data/{library.upper()}/{table.upper()}/rows?limit=100000"
        headers = {'Authorization': 'Bearer ' + access_token}
        try:
            response = requests.request('GET', url, headers=headers, verify=False)#certifi.where()
            if response.status_code == 200:
                data = response.json()
                results_objects['data'] = data['items']
                print('SAS data was retrieved successfully!')
            else:
                print(f"Failed to retrieve SAS data: {response.text}")
        except:
            print('Unable to retrieve SAS data.')

    return results_objects

def save_results_to_files(results, base_name="sas_results"):
    """
    Save SAS job outputs to local files.

    Parameters
    ----------
    results : dict
        Dictionary containing job results. Expected keys:
        - 'log': List of log lines as dictionaries with a "line" key.
        - 'results': List of JSON objects holding ODS output.
        - 'data': List of data rows; each row is a dictionary with a "cells" key holding cell values.
    base_name : str, optional
        Base name for the output files. Output files generated are:
          - <base_name>_log.txt: Contains SAS log lines.
          - <base_name>_results.txt: Contains JSON-formatted ODS results.
          - <base_name>_data.csv: Contains SAS data table rows in CSV format.

    Returns
    -------
    None
        Files are written to the current directory.
    """
    # Save SAS log
    with open(f"{base_name}_log.txt", "w") as f:
        for line in results.get("log", []):
            f.write(line.get("line", "") + "\n")
    # Save ODS results
    with open(f"{base_name}_results.txt", "w") as f:
        for item in results.get("results", []):
            f.write(json.dumps(item, indent=2) + "\n")
    # Save data as CSV
    if "data" in results:
        data = results.get("data", [])
        if data: 
            # Define column names based on the base_name
            if base_name == "employee_analysis":
                column_names = ['EmpID', 'FirstName', 'LastName', 'Salary', 'SalaryGroup', 'Department']
            elif base_name == "department_summary":
                column_names = ['Department', 'EmpCount', 'AvgSalary', 'MinSalary', 'MaxSalary']
            else:
                column_names = list(data[0].get("cells", {}).keys())
            
            with open(f"{base_name}_data.csv", "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)
                for row in data:
                    writer.writerow(row.get("cells", {}))
    print("Output saved to files:", f"{base_name}_log.txt", f"{base_name}_results.txt", f"{base_name}_data.csv")

# Run the tests
if __name__ == "__main__":
    print("SAS Viya Server Test")
    print("=" * 50)
    
    # Check for environment variables first
    if not sasserver or not access_token or access_token == "YOUR_TOKEN_HERE":
        print("ERROR: Please set the SAS_SERVER_URL and SAS_ACCESS_TOKEN environment variables.")
    else:
        connection_data = test_connection()
        if connection_data:
            session_id = create_sas_session()
            job_id = submit_sas_code(session_id, sas_code=[
                '''/* Create initial dataset */
                data work.employee_data;
                   input EmpID $ FirstName $ LastName $ Salary Department $;
                   datalines;
                   E001 John Smith 155000 Sales
                   E002 Mary Johnson 162000 IT
                   E003 David Williams 148000 HR
                   E004 Sarah Brown 171000 IT
                   E005 Michael Davis 153000 Sales
                   E006 Lisa Anderson 169000 HR
                   E007 James Wilson 157000 Sales
                   E008 Emily Taylor 163000 IT
                   E009 Robert Martin 152000 HR
                   E010 Susan White 166000 Sales
                   ;
                run;

                /* Use PROC SQL for analysis */
                proc sql;
                   create table work.dept_summary as
                   select Department, 
                          count(*) as EmpCount,
                          avg(Salary) as AvgSalary,
                          min(Salary) as MinSalary,
                          max(Salary) as MaxSalary
                   from work.employee_data
                   group by Department;
                quit;

                /* Create a format using PROC FORMAT */
                proc format;
                   value salarygrp
                      low-150000='Entry Level'
                      150000-165000='Mid Level'
                      165000-high='Senior Level';
                run;

                /* Combine and format the results */
                data work.final_report;
                   set work.employee_data;
                   format Salary dollar10. SalaryGroup $20.;
                   SalaryGroup = put(Salary, salarygrp.);
                run;

                /* Print the results */
                proc print data=work.final_report noobs;
                   title 'Employee Salary Analysis';
                   var EmpID FirstName LastName Salary SalaryGroup Department;
                run;

                proc print data=work.dept_summary noobs;
                   title 'Department Summary Statistics';
                   format AvgSalary MinSalary MaxSalary dollar10.;
                run;'''
            ])
            
            if job_id:
                state = check_job_submission_status(session_id, job_id)
                print(f"The code submission finished with the status: {state}")
                
                # Get both final_report and dept_summary results
                results_report = get_job_results(session_id, job_id, library='work', table='final_report')
                results_summary = get_job_results(session_id, job_id, library='work', table='dept_summary')
                
                # Save both results
                save_results_to_files(results_report, "employee_analysis")
                save_results_to_files(results_summary, "department_summary")
                print("Results saved to files.")