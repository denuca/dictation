# api/webhook.py
import os
import requests
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'  # Temporary folder for file uploads

@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        data = request.form
        name = data.get('name')
        file = request.files['file']

        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Read the file content
        with open(file_path, 'r') as f:
            file_content = f.read()

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {os.getenv("GITHUB_TOKEN")}'
        }

        payload = {
            'ref': 'main',
            'inputs': {
                'name': name,
                'file': file_content # Pass the file content as an input
                }
        }

        response = requests.post(
            'https://api.github.com/repos/denuca/dictation/actions/workflows/121155771/dispatches',
            json=payload,
            headers=headers
        )

        print(response)
        print(response.status_code)
        print(response.text)
        #os.system(f"response: {response}.")
        #os.system(f"response.status_code: {response.status_code}.")
        #os.system(f"response.text: {response.text}.")

        # The dispatches is a success
        if response.status_code == 204:
            #os.system(f"response.status_code == 204.")
            print(f"response.status_code == 204.")
            print(f"headers: {headers}")
            #print(f"payload: {payload}")
            # But doesn't return the run details...
            # Get the run details
            workflow_runs_response = requests.get(
                'https://api.github.com/repos/denuca/dictation/actions/workflows/121155771/runs',
                headers=headers
            )

            #print(f"workflow_runs: {workflow_runs.text}")

            #workflow_runs = response.json().get('workflow_runs', [])
            if workflow_runs_response.status_code == 200:
                print(f"workflow_runs_response.status_code == 200")
                # Get the most recent run_id
                workflow_runs = workflow_runs_response.json().get('workflow_runs', [])
                most_recent_run_id = workflow_runs[0]['id']
                print(f'Most recent run ID: {most_recent_run_id}')
            else:
                print('No workflow runs found.')
            # Poll for the workflow run status
            run_id = most_recent_run_id #response.json().get('id')
            artifact_url = None

            #print(f'Starting Poll...')
            #for _ in range(10):  # Poll up to 10 times
            #    print(f'Polling...')
            #    time.sleep(5)  # Wait for 5 seconds between polls
            #    print(f'Polling after sleep...')
            run_response = requests.get(
                f'https://api.github.com/repos/denuca/dictation/actions/runs/{run_id}/artifacts',
                headers=headers
            )
            print(f"run_response: ({run_response.status_code} - {run_response.json()}")
            if run_response.status_code == 200:
                print(f"run_response.status == 200")
                artifacts = run_response.json().get('artifacts', [])
                artifact_id = artifacts[0]['id']

                #print(f"artifacts@ {artifacts}")
                # Loop through the artifacts to print their names and URLs
                #for artifact in artifacts:
                #    # Each artifact is a dictionary
                #    artifact_name = artifact.get('name')
                #    artifact_download_url = artifact.get('archive_download_url')
                #    print(f"Name: {artifact_name}, URL: {artifact_download_url}")

                artifact_url = f"https://github.com/denuca/dictation/actions/runs/{run_id}/artifacts/{artifact_id}"
                print(f"artifact_url: {artifact_url}")

            if artifact_url:
                return jsonify({'message': 'GitHub Action triggered successfully!', 'download_link': artifact_url}), 200
            else:
                return jsonify({'message': 'GitHub Action triggered, but artifact URL could not be retrieved.'}), 200
        else:
            print("echo 'This is a message logged in GitHub Actions.'")
            return jsonify({'message': 'Failed to trigger GitHub Action', 'error': response.text}), 500
    except Exception as e:
        #os.system(f'Error processing webhook: {str(e)}')
        print(f'Error processing webhook: {str(e)}')
        return jsonify({'message': 'Error processing webhook.', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)