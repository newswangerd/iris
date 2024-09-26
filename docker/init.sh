#!/bin/bash

# Full path to the file
FILE_PATH="/etc/iris/certs/key.pem"

# Check if the file exists
if [ ! -f "$FILE_PATH" ]; then
    mkdir -p "/etc/iris/certs/"
    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
        -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=iris" \
        -keyout /etc/iris/certs/key.pem  -out /etc/iris/certs/cert.pem
    echo "New self signed SSL certificate generated successfully."
else
    echo "Certificate file already exists at $FILE_PATH"
fi


python /opt/iris/docker/init_admin.py
python /opt/iris/src/iris/server/app.py
