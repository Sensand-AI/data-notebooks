import os

import papermill as pm
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    # Simple health check endpoint
    return jsonify({"status": "ok"}), 200

@app.route('/run-notebook', methods=['POST'])
def run_notebook():
    # Extract parameters from the POST request
    data = request.json
    notebook_name = data.get('notebook_name', 'input_notebook.ipynb')
    output_name = data.get('output_name', 'output_notebook.ipynb')
    parameters = data.get('parameters', {})

    # Construct notebook paths
    input_path = os.path.join('/workspaces/data-notebooks/notebooks', notebook_name)
    output_path = os.path.join('/workspaces/data-notebooks/notebooks', output_name)


    # Execute the notebook with Papermill
    try:
        pm.execute_notebook(
            input_path,
            output_path,
            parameters=parameters
        )
        return jsonify({"message": "Notebook executed successfully", "output_notebook": output_path}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
