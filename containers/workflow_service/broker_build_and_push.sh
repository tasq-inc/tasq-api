#!/usr/bin/env bash

dockerfilename=brokerDockerfile
region=us-east-2
image=tasq-assign-user-tasks-broker
version="dev"
#$(git rev-parse --abbrev-ref HEAD)

if [ "$image" == "" ];
then
    image=$(basename `git rev-parse --show-toplevel`)
fi


# Get the account number associated with the current IAM credentials
account=$(aws sts get-caller-identity --query Account --output text)

if [ $? -ne 0 ];
then
    exit 255
fi

fullname="${account}.dkr.ecr.${region}.amazonaws.com/${image}:${version}"

# If the repository doesn't exist in ECR, create it.

aws ecr describe-repositories --repository-names "${image}" > /dev/null 2>&1

if [ $? -ne 0 ];
then
    aws ecr create-repository --repository-name "${image}" > /dev/null
fi

# Get the login command from ECR and execute it directly
$(aws ecr get-login --region ${region} --no-include-email)

# Build the docker image locally with the image name and then push it to ECR
# with the full name.

docker build -t ${image} -f ${dockerfilename} --build-arg DEPLOY_STAGE=${version} .
docker tag ${image} ${fullname}

docker push ${fullname}

# Cleanup: Remove image locally
docker images ${account}.dkr.ecr.${region}.amazonaws.com/${image} --filter "dangling=true" | awk '{print $3}' | xargs docker rmi -f
