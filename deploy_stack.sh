#!/usr/bin/env bash
VERSIONTAG=$(git describe --tags --long)
CI_ENVIRONMENT_NAME=$(git rev-parse --abbrev-ref HEAD)
echo "Version Tag is :"$VERSIONTAG
echo "CI stage is: "$CI_ENVIRONMENT_NAME
echo "hmm 1"
npm i -g serverless@2.32.0 npm@latest
echo "hmm 2"
# npm install
npm i serverless-latest-layer-version --save-dev
echo "hmm 3"
npm i serverless-plugin-ifelse --save-dev
echo "hmm 4"
npx serverless --aws-profile default deploy --force --stage ${CI_ENVIRONMENT_NAME} --versiontag ${VERSIONTAG} --uploadinitialfiles True
echo "hmm 5"