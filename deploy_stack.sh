#!/usr/bin/env bash
VERSIONTAG=$(git describe --tags --long)
short_commit_hash=$(git log --pretty=format:'%h' -n 1)
full_commit_hash=$(git rev-parse $short_commit_hash)
BRANCH_NAME_STRING=$(git name-rev --name-only --exclude=tags/* $full_commit_hash)
# Split the string on a forward slash "/", then grab the last element in the array
CI_ENVIRONMENT_NAME="${BRANCH_NAME_STRING##*/}"

CONTAINER_TAG=${CI_ENVIRONMENT_NAME}

if [ "${CI_ENVIRONMENT_NAME}" == "prod" ];
then
    CONTAINER_TAG=latest
fi


echo $CONTAINER_TAG
echo "Version Tag is :"$VERSIONTAG

# npm install -g serverless
# npm install
npx serverless --aws-profile default deploy --force --verbose --stage ${CI_ENVIRONMENT_NAME} --containerTag ${CONTAINER_TAG} --versiontag ${VERSIONTAG} --uploadinitialfiles True
