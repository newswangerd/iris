#!/bin/bash

# Full path to the file
FILE_PATH="/mount/certs/key.pem"

# Check if the file exists
if [ ! -f "$FILE_PATH" ]; then
    mkdir -p "/mount/certs/"
    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
        -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=iris" \
        -keyout //mount/certs/key.pem  -out /mount/certs/cert.pem
    echo "New self signed SSL certificate generated successfully."
else
    echo "Certificate file already exists at $FILE_PATH"
fi


/opt/env/bin/python /opt/scripts/init_admin.py
/opt/env/bin/python /opt/iris/iris/server/app.py
