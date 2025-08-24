#base image
FROM python:3.10-slim

#work directory
WORKDIR /app

#copy
COPY . /app

#run 
RUN pip install -r requirements.txt

#expose
EXPOSE 8501

#cmd
CMD ["streamlit","run","app.py"]
