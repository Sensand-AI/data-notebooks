# data-notebooks

This repository hosts Jupyter notebooks that perform geospatial and earth observation tasks. These notebooks are used for exploring new ideas, experimental data science, and some are refined for production use. The repository also includes an AWS Lambda function under `lambdas/notebook-executor` to trigger notebooks in our cloud ecosystem.

All notebooks are under `/notebooks`. Existing lambda code outside of that directory is work that is tangential and kept purely for archival purposes.

This repository also includes the custom python packages used internall at Sensand, `aws_utils` and `sensand_gis_utils`.

## Repository Structure

- `notebooks/`: Contains Jupyter notebooks for exploration and experimentation.
- `production/`: Contains refined notebooks ready for production use.
- `templates/`: Contains template notebooks for users to copy and work from.
- `packages/`: Contains custom python packages developed and used internally for geospatial processes.
- `lambda/`: Contains the AWS Lambda function to trigger production notebooks.
- `.devcontainer/`: Configuration for the development container.
- `.buildkite/`: Configuration for buildkite.

** You will find individual `README.md` files in these directories that provide instructions tailored to the contents of the directories.**

## Remote Sensing Datasets

[A list of Remote Sensing Datasets in Notion](https://www.notion.so/sensandworkspace/Remote-Sensing-Datasets-18aebbc192104af8a5062ce843a4faf4).


## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:
- [Visual Studio Code](https://code.visualstudio.com/) installed
- [Docker](https://www.docker.com/products/docker-desktop) installed
- [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for VS Code

#### Additional requirements for testing notebooks for deployment

- Postman (needed for testing notebook outputs using the `notebook-executor`)
- aws-vault (for updating the GIS image in ECR and running the `notebook-executor`)

### Setting Up the Devcontainer (recommended)

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:sensand/data-notebooks.git
   cd data-notebooks
   ```

2. **Open in VS Code**:
   - Make sure you have Docker or Docker Desktop installed on your local machine, and that it us running.
   - Open the project folder in Visual Studio Code.
   - VS Code might prompt you to reopen the project in a container. If so, click "Reopen in Container". Otherwise, use the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on Mac) and select "Remote-Containers: Open Folder in Container..."

3. **Wait for the Container to Build**:
   - The first time you open the project, VS Code will build the devcontainer. This process can take up to 15 minutes so please be patient. It will be much faster after the first run.

4. **Install dependencies**:
   - The dependencies are listed in `requirements-core.txt`, `requirements-jupyter.txt` and `requirements-custom.txt`. They will be installed automatically when the development container is built.


## Contributing

If you'd like to explore Jupyter and create your own notebook:

1. Fork this repository.
2. Create a branch: `git checkout -b [branch_name]`.
3. Make your changes and commit them: `git commit -m '[commit_message]'`
4. Push to the original branch: `git push origin [project_name]/[location]`
5. Create the pull request.

Once you have forked the repository and built the dev container (see instructions above) you have two options for working with jupyter notebooks:

### Writing notebook code inside Vscode

The dev container comes with several jupyter extensions installed so that you can create and work on jupyter notebooks in your local Vscode environment. 

It is recommended to copy one of the templates from the templates folder `notebooks/templates` and rename it and use this as your starting point. If you do not want to work from a template, you can create a new file and give it the file extension `.ipynb`. This will create a new, blank jupyter notebook for you to work in.

#### Installing experimental packages inside a Jupyter Notebook

If you are experimenting with a python package, instead of adding it to one of the requirements txt files, you can install it directly within the notebook. Doing this means you do not have to rebuild the devcontainer. There are instructions included in the template notebooks as well.

1. Create a new code cell in your notebook at the very top of the notebook
2. use `%pip install [package-name] -q`
   - the `-q` flag stops the tex outputs from printing below the cell. If you are debugging a package, you can remove the flag.
3. Note that this cell will need to be run at least once for the package to be installed in the notebook for each session, so if you exit the dev container you will need to run it again.

### Using Jupyter server (currently bugged)

1. **Accessing Jupyter Notebook**:
   - The Jupyter server should start automatically if configured in the `devcontainer.json`. You can access it at `http://localhost:8888`.
   - Vscode will also allow you to run the notebook from within the editor window

2. **Working with Notebooks**:
   - Open and run Jupyter notebooks as you would normally. All changes made within the devcontainer will be reflected in your project directory.


### Installing new python packages

See instructions above about temporarily installing python packages within Jupyter Notebooks for experimentation. If you have determied that a package is needed for multiple notebooks, or is required for a production notebook, you can add them permanently.

There are multiple `requirements-*.txt` files in the project. Each file is used for a different purpose.

- `requirements-core.txt` contains core packages that are used in development and production. Packages in this file are also installed in the custom Docker Image that is held in AWS ECR. Do not add new packages to this file unless ou have consulted with the DGIS team and confirmed the packages are required for, and safe to use, in deployment.
- `requirements-jupyter.txt` is used to install packages for the Jupyter notebook and for the `notebook-executor` lambda function.
- `requirements-custom.txt` contains custom packages that are not available in the public PyPi repository.
- `requirements-dev.txt` contains packages used for development purposes.

Add your python package to `requirements-jupyter.txt`. You must include a comment on what that package is and what it does. Include the package version.

After adding the package, you must rebuild the devcontainer. You can do this by running the `Remote-Containers: Rebuild Container` command from the command palette.

Note: The `notebook-executor` lambda function is used to run Jupyter notebooks as AWS Lambda functions. It is imperative that your package is compatible with AWS Lambda.

### Missing `.env` and adding secrets

Create a `.env` file in the root project directory based off `.env.example` containing the actual secret values.

You can find the values in `(env) data-notebooks` in the 1Password Engineering Vault. If adding a new secret value, add it here as well.


## Using the Devcontainer with Jupyter

### 1. Connecting to the jupyter kernel (Yes, VSCode's process is a bit convoluted - I can't store the kernel in settings.json for some reason) (check this is still up to date)

`./start-juptyer.sh` will start the jupyter notebook server. A token is applied `vscode` and the server is started on port `8888`.

In order for VSCode to connect to the jupyter kernel, you must have the `jupyter` extension installed. Once installed, you can connect to the kernel by clicking on the `Jupyter` icon in the left sidebar and selecting the notebook you want to open.

Click on the Kernel dropdown on the top right of the notebook and select the kernel you want to use. Click `Select another kernel` and then `Select Jupyter Server`. 

Enter the URL of the jupyter server (http://jupyter:8888/?token=vscode) and click `Connect`.

You will get another prompt to select the kernel. Select the kernel listed with `ipykernel`.


## Testing notebook executor outputs

Make sure you have Postman installed prior to doing this. You may also need `aws-vault` and access to some sensand environments. If you need access to these, please organise this with the head of engineering.

- in terminal run `docker compose build notebook-executor` and `docker compose up notebook-executor` to ensure container is up to date
- in Postman, set up a new collection and create a `POST` request using the port that the docker container is mapped to
   - This url: `http://localhost:9002/2015-03-31/functions/function/invocations`
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


## Unit testing

Please ensure your custom packages have a `test_[filename].py` which includes unit tests for the functions in the package.

These tests are run automatically in the buildkite pipeline, and can be run locally using the following command in a terminal: `pytest`


## Updating the GIS base image

To update the base image, add additional packages to `requirements-core.txt`.
After committing the changes, you must manually trigger the base image build step (in Buildkite at the bottom).
Since prior build steps use this base image, please Rebuild the pipeline (in Buildkite, top right).