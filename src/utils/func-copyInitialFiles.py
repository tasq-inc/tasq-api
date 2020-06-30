
import boto3
import os
import glob
from zipfile import ZipFile, ZipInfo
from io import BytesIO

s3 = boto3.client('s3')
bucket = os.getenv("EnvS3LambdaBucketTarget")
uploadInitialFiles = os.getenv("EnvUploadInitialFiles")

print(uploadInitialFiles)

def uploadLambdaScripts(event, context):
    if uploadInitialFiles:
        path = 'src/functions'
        path_dirs = os.listdir(path)

        for p in path_dirs:
            path_iter = os.path.join(path, p)

            file_list = glob.glob(path_iter + "/**", recursive=True)

            inMemoryOutputFile = BytesIO()

            zipFile = ZipFile(inMemoryOutputFile, 'w')
            for f in file_list:
                if not os.path.isdir(f):
                    with open(f, "rb") as file:
                        fileb = file.read()
                        zip_path = f.split(path_iter + "/")[1]

                        zinfo = ZipInfo(zip_path)
                        zinfo.external_attr = 0o777 << 16
                        zipFile.writestr(zinfo, fileb)

            zipFile.close()

            inMemoryOutputFile.seek(0)

            s3.put_object(Bucket=bucket,
                          Key="-".join([os.getenv("EnvS3LambdaKeyTarget"), p + ".zip"]),
                          Body=inMemoryOutputFile)

        return 'Files uploaded to ' + os.getenv("EnvS3LambdaBucketTarget") + ' successfully!'

    else:
        return 'EnvUploadInitialFiles set to False. Skipping uploading to ' + os.getenv("EnvS3LambdaBucketTarget") + '.'

