import sys
import os
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# Initiate the spark session context
args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Assign the bucket name
bucket_name = os.environ["CUSTOMER_BUCKET_NAME"]

# Load the data set from Amazon S3 into a dynamic data frame
load_data = glueContext.create_dynamic_frame.from_options(
    format_options={"quoteChar": '"', "withHeader": True, "separator": ","},
    connection_type="s3",
    format="csv",
    connection_options={"paths": [f"s3://{bucket_name}"]},
    transformation_ctx="load_data",
)

# Convert the dynamic frame to a data frame
df = load_data.toDF()

# Create a "user defined function" and define a python lambda for data cleaning. Example: Removing unwanted characters such as '%' and ' ' white spaces
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

chop_f = udf(lambda x: x.replace("%", "").replace(" ", ""), StringType())
clean_df = df.withColumn("COLUMN 1", chop_f(df["COLUMN 1"])).withColumn(
    "COLUMN 2", chop_f(df["COLUMN 2"])
)

# Convert the data frame back to a dynamic frame
from awsglue.dynamicframe import DynamicFrame

df_tmp = DynamicFrame.fromDF(clean_df, glueContext)

# Now we can update the schema of the dynamic frame. Example: Change column names and typecast columns
schema_update = ApplyMapping.apply(
    frame=df_tmp,
    mappings=[
        ("COLUMN 1", "string", "COLUMN_1", "string"),
        ("COLUMN 2", "string", "COLUMN_2", "float"),
    ],
    transformation_ctx="schema_update",
)

# Write the data back to Amazon S3 in parquet format
write_data = glueContext.getSink(
    path=f"s3://{bucket_name}/data-proc/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=["COLUMN_1"],
    enableUpdateCatalog=True,
    transformation_ctx="write_data",
)
write_data.setCatalogInfo(catalogDatabase="data_set_db", catalogTableName="data_proc")
write_data.setFormat("glueparquet", compression="snappy")
write_data.writeFrame(schema_update)
job.commit()
