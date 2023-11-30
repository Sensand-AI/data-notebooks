# data-notebooks

Collection of data and geoscience related notebooks.

All notebooks are under `/notebooks`. Existing lambda code outside of that directory is work that is tangential and kept purely for archival purposes.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- [Visual Studio Code](https://code.visualstudio.com/) installed
- [Docker](https://www.docker.com/products/docker-desktop) installed
- [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for VS Code

## Setting Up the Devcontainer

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

