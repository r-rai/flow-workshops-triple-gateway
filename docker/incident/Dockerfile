FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
COPY src/demo/incident_sandbox.py /incident_sandbox.py
USER 65534:65534
CMD ["python", "/incident_sandbox.py"]
