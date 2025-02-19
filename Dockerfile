# Use dev-container as the base image
FROM localhost:5001/dev-container:latest 

# Set an environment variables
ENV PROJECT_WORKDIR=/home/dev-container/iac/alpha-neuron

RUN echo "-- Building iac image" \
 && mkdir -p $PROJECT_WORKDIR \
 && chmod u+rwX $PROJECT_WORKDIR \
 && chown -R dev-container $PROJECT_WORKDIR \
 && chgrp -R dev-container $PROJECT_WORKDIR \
 && sudo mkdir -p /Users/dinindu/Projects/GitHub

# this relies on .dockerignore for filtering
COPY . $PROJECT_WORKDIR

WORKDIR $PROJECT_WORKDIR

ENTRYPOINT ["/bin/bash"]
