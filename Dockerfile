FROM python:3.11

RUN wget -O - https://apt.corretto.aws/corretto.key | gpg --dearmor -o /usr/share/keyrings/corretto-keyring.gpg && \
        echo "deb [signed-by=/usr/share/keyrings/corretto-keyring.gpg] https://apt.corretto.aws stable main" | tee /etc/apt/sources.list.d/corretto.list

RUN apt-get update && apt-get install -y java-11-amazon-corretto-jdk && rm -rf /var/lib/apt/lists/*

WORKDIR /apps

RUN mkdir /anvil-data

RUN useradd anvil
RUN chown -R anvil:anvil /anvil-data
USER anvil

ENTRYPOINT []

USER root

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
# Add the below just in case the preceding pip install changes the version of
# anvil-app-server
RUN anvil-app-server || true
EXPOSE 3030

USER anvil
COPY --chown=anvil:anvil . /apps/Template2050Calculator/
