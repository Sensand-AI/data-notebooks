# Notebook templates for jupyter data notebooks used at Sensand

Jupyter notebooks are awesome tools: they enable fast prototyping and easy result sharing. However, due to their flexibility, they are prone to be abused.

In order to help keep Sensand's notebooks clean and properly formatted for moving to production pipelines, This folder of templates has been created. The template is also a productivity tool, speeding up common setup, such as library import and configuration.

# Using the templates

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


# parameters and Tags
Nav to fill out this section with short explanation of tags and parameters