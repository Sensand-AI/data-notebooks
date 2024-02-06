# FROM lambci/lambda:build-python3.9
FROM public.ecr.aws/lambda/python:3.8

# WORKDIR /var/task


COPY requirements*.txt ${LAMBDA_TASK_ROOT}
COPY app.py ${LAMBDA_TASK_ROOT}

# RUN -m pip install --upgrade --force-reinstall pip
RUN -m pip install -r requirements-pre.txt
RUN -m pip install -r requirements.txt