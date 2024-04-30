# data-notebooks

Collection of data and geoscience related notebooks.

All notebooks are under `/notebooks`. Existing lambda code outside of that directory is work that is tangential and kept purely for archival purposes.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- [Visual Studio Code](https://code.visualstudio.com/) installed
- [Docker](https://www.docker.com/products/docker-desktop) installed
- [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for VS Code

## Option 1: Setting Up the Devcontainer

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:sensand/data-notebooks.git
   cd data-notebooks
   ```

2. **Open in VS Code**:
   - Open the project folder in Visual Studio Code.
   - VS Code might prompt you to reopen the project in a container. If so, click "Reopen in Container". Otherwise, use the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on Mac) and select "Remote-Containers: Open Folder in Container..."

3. **Wait for the Container to Build**:
   - The first time you open the project, VS Code will build the devcontainer. This process can take a few minutes.

## Option 2: Run with docker-compose
1. **Clone the Repository**:
   ```bash
   git clone git@github.com:sensand/data-notebooks.git
   cd data-notebooks
   ```

2. **Open in VS Code**:
   - Open the project folder in Visual Studio Code.
   - VS Code might prompt you to reopen the project in a container. **DON'T**
   - Open a terminal in VS Code and run `docker compose up jupyter`

## Using the Jupyter Notebook

Once the devcontainer is up and running:

1. **Accessing Jupyter Notebook**:
   - The Jupyter server should start automatically if configured in the `devcontainer.json`. You can access it at `http://localhost:8888`.
   - Vscode will also allow you to run the notebook from within the editor window

2. **Working with Notebooks**:
   - Open and run Jupyter notebooks as you would normally. All changes made within the devcontainer will be reflected in your project directory.

## Contributing

If you'd like to explore Jupyter and create your own notebook:

1. Fork this repository.
2. Create a branch: `git checkout -b [branch_name]`.
3. Make your changes and commit them: `git commit -m '[commit_message]'`
4. Push to the original branch: `git push origin [project_name]/[location]`
5. Create the pull request.

### Installing new python packages

There are multiple `requirements-*.txt` files in the project. Each file is used for a different purpose.

- `requirements-jupyter.txt` is used to install packages for the Jupyter notebook and for the `notebook-executor` lambda function.
- `requirements-custom.txt` contains custom packages that are not available in the public PyPi repository.
- `requirements-dev.txt` contains packages used for development purposes.

Add your python package to `requirements-jupyter.txt`. You must include a comment on what that package is and what it does.

After adding the package, you must rebuild the devcontainer. You can do this by running the `Remote-Containers: Rebuild Container` command from the command palette.

Note: The `notebook-executor` lambda function is used to run Jupyter notebooks as AWS Lambda functions. It is imperative that your package is compatible with AWS Lambda.

### Missing `.env` and adding secrets

Create a `.env` file in the root project directory based off `.env.example` containing the actual secret values.

You can find the values in `(env) data-notebooks` in the 1Password Engineering Vault. If adding a new secret value, add it here as well.

## Remote Sensing Datasets

[A list of Remote Sensing Datasets in Notion](https://www.notion.so/sensandworkspace/Remote-Sensing-Datasets-18aebbc192104af8a5062ce843a4faf4).

## Using the Devcontainer with Jupyter

### 1. Connecting to the jupyter kernel (Yes, VSCode's process is a bit convoluted - I can't store the kernel in settings.json for some reason)

`./start-juptyer.sh` will start the jupyter notebook server. A token is applied `vscode` and the server is started on port `8888`.

In order for VSCode to connect to the jupyter kernel, you must have the `jupyter` extension installed. Once installed, you can connect to the kernel by clicking on the `Jupyter` icon in the left sidebar and selecting the notebook you want to open.

Click on the Kernel dropdown on the top right of the notebook and select the kernel you want to use. Click `Select another kernel` and then `Select Jupyter Server`. 

Enter the URL of the jupyter server (http://jupyter:8888/?token=vscode) and click `Connect`.

You will get another prompt to select the kernel. Select the kernel listed with `ipykernel`.


## Testing notebook executor outputs

- in terminal run `docker compose build notebook-executor` and `docker compose up notebook-executor` to ensure container is up to date
- in Postman, set up a new collection and create a `POST` request using the port that the docker container is mapped to
   - e.g. `http://localhost:9002/2015-03-31/functions/function/invocations`
- Make sure the 'body' of the request is set to JSON and add the following (note geometry not included in example):
```{
    "notebook_name": "dem",
    "save_output": true,
    "output_type": "overlay",
    "parameters": {
        "propertyName": "ncaorana",
        "start_date": "2023-01-01",
        "end_date": "2023-03-01",
        "geojson": {...
```
- Send the postman request. It should timeout after 180 second and return a response. In the response there will be a presigned url link.
- download the tiff from the link and open it in QGIS to test.