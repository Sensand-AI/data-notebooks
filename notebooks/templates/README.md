# Notebook templates for jupyter data notebooks used at Sensand

Jupyter notebooks are awesome tools: they enable fast prototyping and easy result sharing. However, due to their flexibility, they are prone to be abused.

In order to help keep Sensand's notebooks clean and properly formatted for moving to production pipelines, This folder of templates has been created. The template is also a productivity tool, speeding up common setup, such as library import and configuration.

# Using the templates
## Exploration and Execution templates

**There are two types of notebook templates - exploration and execution.**

**Exploration** templates should be used when developing new data products, and enable fast data exploration, testing, visualisation and internal demo-ing.

**Execution** notebooks (and the execution templates) have more strict requirements. These notebook need to be parametized for production. Examples are included in the template.

## Parameter definition and tags

For execution notebooks to work, both `papermill comments` and `cell tags` must be included for each cell in the notebook. `Papermill comments` are different to regular comments, though the syntax is the same. Take care to not remove the papermill comments when cleaning up a notebook for production.

### Parameter cell
One cell must be designated `parameters`. This cell must have BOTH the `papermill comment` designating it as the aprameters cell, and the `tag`

Example:

#### papermill comment:
`papermill_description=parameters`

#### Jupyter tags in vscode:
- use the 'more actions' button in the top right of a cell to access tags
- select `add cell tag`
- make cell tag `parameters`


These templates should not be edited directly. Please make a copy of the template and move it to the apprioriate sub-directory before you begin working.

## Installing python packages not included in the repository environment

Packages can be installed within the notebook, rather than being added to the devcontainer. An example is included in the template to demonstrate how to do this.

It is important to keep the notebook development space and the production lambdas the same, so packages should be agreed on by the team before being added.
Adding new packages to any of the `*-requirements.txt` also requires the devcontainer to be rebuilt.

## The template has to following sections mapped out

 - preamble with sections for defining the notebook purpose, methodology, WIP items to be implemented
 - Package installation and importing
 - Functions
 - Data Import
 - Data processing
 - Data visualisation and exporting
