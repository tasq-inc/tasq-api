import boto3
import time
import pandas as pd
import warnings
import decimal
from tqdm import tqdm
from uuid import uuid4
from joblib import Parallel, delayed

from helpers.worker_helpers import get_enabled_wells, get_metadata, read_parquet, get_matching_s3_keys, write_dynamodb
from helpers.feature_engineering import find_state_change

table_meta = "MetaDataStore"
s3_bucket = "tasq-prod-ts-store"
s3_prefix = "ts_features"
# dynamodb_dest = "tasq-detect-state-change-dev-PredictionTable-1MUGFIP6Y64XO"
dynamodb_dest = "tasq-detect-state-change-prod-PredictionTable-1RDBTM2WA655Y"

def parallel_func(n, d, f, df_meta):
    files = df_meta[(df_meta["NodeID"] == n) & (df_meta["Description"] == d) & (df_meta["Feature"] == f)]
    files = files["files"].to_list()

    try:
        df = read_parquet(files)
    except:
        return None

    msg_dict = {
        "node_id": n,
        "description": d,
        "Feature": f
    }

    
    result_dict = find_state_change(df, {"Feature": f})

    if isinstance(result_dict, dict):
        ### Prep payload
        with decimal.localcontext(boto3.dynamodb.types.DYNAMODB_CONTEXT) as ctx:
            ctx.traps[decimal.Inexact] = False
            ctx.traps[decimal.Rounded] = False
            decimal.getcontext().prec = 4
            for k, v in result_dict.items():
                if isinstance(v, float):
                    result_dict[k] = ctx.create_decimal_from_float(v)

        payload = {
                "PredictionID": str(uuid4()),
                "PredictionType": "state change",
                "StateChangeDate": result_dict["StateChangeDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                "time": df.iloc[-1]["time"].strftime("%Y-%m-%dT%H:%M:%S"),
                "NodeID": msg_dict["node_id"],
                "States": [{
                    "Description": msg_dict["description"],
                    "Feature": msg_dict["Feature"],
                    "pre_state": result_dict["pre_state"],
                    "post_state": result_dict["post_state"],
                    "delta_state": result_dict["delta_state"],
                    "state_units": result_dict["state_units"]
                }]
            }

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = write_dynamodb(payload, dynamodb_dest)
            print(result)


s3_prefix_path = "{}/Operator=Enerplus/NodeID={}"

while True:
    well_list = get_enabled_wells(table_meta)

    df_meta = get_metadata(s3_bucket, "{}/Operator=Enerplus".format(s3_prefix))
    df_meta = df_meta[df_meta["NodeID"].isin(well_list)]
    df_partitions = df_meta[["NodeID", "Description", "Feature"]].drop_duplicates()

    node_desc_feat = list(zip(df_partitions["NodeID"], df_partitions["Description"], df_partitions["Feature"]))

    Parallel(n_jobs=-1)(delayed(parallel_func)(n, d, f, df_meta) for n, d, f in tqdm(node_desc_feat))

    print("Next Patrol in 3 hours...")
    time.sleep(60*60*3)