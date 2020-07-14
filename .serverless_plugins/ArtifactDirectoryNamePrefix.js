'use strict';

/**
 * Usage:
 *
 *  1. Place this file in your project under the .serverless_plugins directory (if it doesn't exist, create it).
 *  2. Add the following to the end of your serverless.yml file.
 *
 * plugins:
 *   - ArtifactDirectoryNamePrefix
 *
 * custom:
 *   artifactDirectoryNamePrefix: your-bucket-prefix
 */
class ArtifactDirectoryNamePrefix {
  constructor(serverless, options) {
    this.serverless = serverless;
    this.options = options;

    this.hooks = {
      'before:package:compileFunctions': this.compileFunctions.bind(this),
    };
  }

  compileFunctions() {
    const previousDirectoryName = this.serverless.service.package.artifactDirectoryName;
    const configuredPrefix = this.serverless.service.custom.artifactDirectoryNamePrefix;
    this.serverless.service.package.artifactDirectoryName = `${configuredPrefix}/${previousDirectoryName}`;
  }
}

module.exports = ArtifactDirectoryNamePrefix;
