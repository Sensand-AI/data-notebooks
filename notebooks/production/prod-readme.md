# Production notebooks

This repository includes jupyter notebooks that are accessible to the `notebook-executor` lambda and can therefore be attached to a workflow and made available within the SLM platform. 

#### You should not be adding a new noteboook file to this directory without approval from the DGIS team lead and confirmation from the product team that this notebook has been approved to be turned into an application.

## Repository structure

## Prerequisites

### Notebook requirements
- Papermill tags have been applied to each cell. See the templates folder for an example
- a `schema.json` file for that notebook
- You will need to get the notebook set up with a workflow id. This must be done by a member of the engineering team with access to the appropriate databases.
- Ensure that any packages needed by the notebook are installed in the GIS docker image. Depending on your access to ECR, you may need the assistance of a member of engineering
- ensure any graphics and outputs that were being generated within the notebook (for example, a matplotlib graph) are removed or commented out. This can impact run time, and these outputs are not exported from the notebook.

## Process
- The notebook code should be finalised and approved in a PR prior to creating a copy for the production folder
- MAKE A COPY OF THE NOTEBOOK - you should keep a copy within the sandbox directory, so that if you wish to experiment or make changes, you can do it there. Once a notebook file has been created and established in the production folder, it should only be edited to resolve bugs.
- Set up a directory within the production folder with a name that is human readable and contains no spaces. 
- The folder name must be the same as the notebook file name.
- the new directory should contain two files - the notebook `.ipynb` file and a `.json` file called `schema.json`.
- Any parameters that are going to be passed into the notebook (e.g. property name, polygon, depth) must be included in both the `schema.json` and the `parameters` cell of the notebook (see template ipynb file for example of how to include papermill parameters)

## Testing

### Requirements
- Postman
- aws-vault and access to the `senstag` environment and aws ecr if you are required to make updates to the GIS docker image