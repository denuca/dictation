# api/webhook.py
import os
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'  # Temporary folder for file uploads

@app.route('/api/webhook', methods=['POST'])
def webhook():
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

    print(response.status_code)
    print(response.text)

    if response.status_code == 204:
        # Construct the URL to the GithHub Actions run page
        run_url = f"https://github.com/denuca/dictation/actions"
        # GitHub API returns 204 No Content for successful workflow dispatch
        return jsonify({'message': 'GitHub Action triggered successfully! Check the Actions tab for the processed file.', 'download_link': run_url}), 200
    else:
        return jsonify({'message': 'Failed to trigger GitHub Action', 'error': response.text}), 500

if __name__ == '__main__':
    app.run(debug=True)