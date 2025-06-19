FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV RUN_MODE=docker
ENV SECRET_KEY=your_secret_key
CMD ["python", "frontend.py"]
